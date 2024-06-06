import csv
import json
from os import makedirs
from os.path import join
from anything_tracker.multiple.track_histories.TrackHistoryPairs import get_category_subfolder_info
from anything_tracker.visualization.TableAnnoSuppressionResults import get_data


def get_summary_line(file):
    with open(file, "r") as f:
        csv_reader = csv.reader(f)
        line_list = list(csv_reader)
        is_matched_list = [m[7] for m in line_list if m and m[7] and len(m) > 2]
        empty_lines = [m for m in line_list if not m]
        line_idx = len(is_matched_list) -1
        # include the outliers, like file path not match
        # summary should be [YMW, pre character distance, post, all, recall, presicion, f1, note]
        final_line_idx = line_idx + len(empty_lines)
        all_data_num = final_line_idx - 1 # 1 head, 1 summary
        summary_line = line_list[final_line_idx][1:]

    summary = [s for s in summary_line if s]
    match_results = json.loads(summary[0])
    dist_results = json.loads(summary[1])
    dist = float(dist_results["dist"]["avg"])
    recall, presicion, f1 = summary[2: 5] 

    return all_data_num, match_results, dist, recall, presicion, f1

def get_avg_for_subsets(float_1, float_2, digit):
    return format((float(float_1) + float(float_2)) / 2, digit)

def get_data(file_list_1, file_list_2):
    summaries = []
    exact_match = []
    exact_match_num_rate = []
    overlapping = []
    overlapping_num_rate = []
    recalls = []
    presicions = []
    f1s = []
    dists = []
    digit = ".1f"

    for file_1, file_2 in zip(file_list_1, file_list_2): # file 1, 2 --> training, test
        all_data_num_1, match_results_1, dist_1, recall_1, presicion_1, f1_1 = get_summary_line(file_1)
        all_data_num_2, match_results_2, dist_2, recall_2, presicion_2, f1_2 = get_summary_line(file_2)
        matches = match_results_1["Y"] + match_results_2["Y"]
        overlaps = match_results_1["M"] + match_results_2["M"]
        all = all_data_num_1 + all_data_num_2
        matches_rate = format((matches / all) * 100, digit)
        overlaps_rate = format((overlaps / all) * 100, digit)

        dist = get_avg_for_subsets(dist_1, dist_2, digit)
        recall = get_avg_for_subsets(recall_1, recall_2, ".3f")
        presicion = get_avg_for_subsets(presicion_1, presicion_2, ".3f")
        f1 = get_avg_for_subsets(f1_1, f1_2, ".3f")

        exact_match.append(matches)
        exact_match_num_rate.append(f"{matches}({matches_rate}\%)")
        overlapping.append(overlaps)
        overlapping_num_rate.append(f"{overlaps}({overlaps_rate}\%)")
        recalls.append(float(recall))
        presicions.append(float(presicion))
        f1s.append(float(f1))
        dists.append(dist)

    summaries = [exact_match, overlapping, recalls, presicions, f1s, dists, exact_match_num_rate, overlapping_num_rate]
    return summaries

def generate_table(overall_data, caption, label, tex_file):
    row_names = ["Line level diff", "Word level diff", "AnythingTracker"]
    col_names = ["Program elements", "Approaches", "Exact matches", "Overlapping", "Recall", "Precision", "F1-score", "Character distance"]
    the_higher_the_better = [True, False, True, True, True, False]

    latex_table = "\\begin{table*}[htbp]\n\\centering\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{" + "ll" + "".join(["r"] * (len(col_names)-1)) + "}\n"
    latex_table += "\\hline\n"

    latex_table += " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each column
    split_num = 7
    for data in overall_data:
        element_names = data[0]
        data_numbers = data[1:split_num]
        num_rates = data[split_num:]
        for i, col, higher_better in zip(range(split_num), data_numbers, the_higher_the_better):
            if higher_better == True:
                textbf = max(col)
            else:
                textbf = min(col)

            for j, num in enumerate(col):
                if num == textbf:
                    if i < 2:
                        num_rates[i][j] = "\\textbf{" + num_rates[i][j] + "}"
                    else:
                        col[j] = "\\textbf{" + str(col[j]) + "}"

        # replace to the number with rate 
        data_numbers[:2] = num_rates
        # match, ovelapping, recall, presicion, f1, dist = data_numbers
        transposed_data = list(zip(*data_numbers))
        for i, row_data in enumerate(transposed_data):
            latex_table += element_names[i] + " & " + row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

        latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table*}"

    with open(tex_file, "w") as f:
        f.write(latex_table + "\n")

def main():
    # suppression data
    common = join("data", "results", "ase", "measurement_results", "element")
    file_name_base = "measurement_results_element"
    oracle_file_folder = join("data", "converted_data")
    category_subset_pairs = get_category_subfolder_info(oracle_file_folder)

    overall_data = []
    file_list_1 = []
    file_list_2 = []

    elements = []
    i = 1
    for element, subset in category_subset_pairs:
        file_list = [
                join(common, "line", f"{file_name_base}_{element}_{subset}.csv"),
                join(common, "word", f"{file_name_base}_{element}_{subset}.csv"),
                join(common, "at", f"{file_name_base}_{element}_{subset}.csv")]
        if i % 2 != 0:
            file_list_1 = file_list
        else:
            file_list_2 = file_list
            element_level_data = get_data(file_list_1, file_list_2)
            elements.append(element)
            for i in range(len(file_list_1)-1):
                elements.append("")
            element_level_data.insert(0, elements)
            overall_data.append(element_level_data)
            file_list_1 = []
            file_list_2 = []
            elements = []
        i+=1

    caption = "Results on tracking Java program elements"
    label = "results_on_program_element"
    output_dir = join("data", "results", "ase", "table_plots")
    makedirs(output_dir, exist_ok=True)
    tex_file = join(output_dir, "element_comparison_table.tex")

    generate_table(overall_data, caption, label, tex_file)


if __name__=="__main__":
    main()