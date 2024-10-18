import csv
import json
from os import makedirs
from os.path import join

def get_main_table_contents_util(data):
    the_higher_the_better = [True, True, False, True, True, True]
    summaries, num_rates, recall_set = data
    summaries_len = len(summaries)
    replace_len = len(num_rates)
    for i, col, higher_better in zip(range(summaries_len), summaries, the_higher_the_better):
        if higher_better == True:
            textbf = max(col)
        else:
            textbf = min(col)

        for j, num in enumerate(col):
            if num == textbf:
                if i < replace_len: # overlappings, exact mactes
                    num_rates[i][j] = "\\textbf{" + num_rates[i][j] + "}"
                elif i > replace_len: # recall set
                    new_i = i - replace_len - 1
                    recall_set[new_i][j] = "\\textbf{" + str(recall_set[new_i][j]) + "}"
                else: # i == replace_len -> character distance
                    col[j] = "\\textbf{" + str(col[j]) + "}"

    # format to replace the number with rate and keep the numbers tailing zeros for recall_set
    summaries[:replace_len] = num_rates
    summaries[(replace_len+1):] = recall_set
    return summaries

def get_data(file_list):
    summaries = []
    match = []
    match_num_rate = []
    exact_match = []
    exact_match_num_rate = []
    partial_overlaps = []
    dists = []
    digit = ".1f"

    recalls = []
    precisions = []
    f1s = []
    # to keep the tailing zeros after numbers.
    recalls_keep = []
    precisions_keep = []
    f1s_keep = []

    for file in file_list:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            # include the outliers, like file path not match
            all_match_results = [line[6] for line in line_list if line]
            all = len(all_match_results) -2 # 1 head, 1 summary
            summary_line = line_list[-1]
            tmp = [s for s in summary_line if s]
            if len(tmp) < 2:
                summary_line = line_list[-2][7:]

        start_idx = 0 # the index to start the summary split
        # summary should be [YMW, pre character distance, post, all, recall, precision, f1, note]
        summary = [s for s in summary_line if s] 
        if "histogram" in str(summary):
            start_idx = 1
        match_results = json.loads(summary[start_idx])
        e_matches = match_results["Y"]
        partial_overlaps = match_results["M"]
        overlappings = e_matches + partial_overlaps
        overlapping_rate = format((overlappings / all) * 100, digit)
        e_matches_rate = format((e_matches / all) * 100, digit)
        dist_results = json.loads(summary[start_idx+1])
        dist = float(dist_results["dist"]["avg"])
        dists.append(dist)

        match.append(overlappings)
        match_num_rate.append(f"{overlappings} ({overlapping_rate}\%)")
        exact_match.append(e_matches)
        exact_match_num_rate.append(f"{e_matches} ({e_matches_rate}\%)")

        recall, precision, f1 = summary[start_idx+2: start_idx+5] 
        # the float() will truncate the tailing zeros, but we need to compare the numbers
        recalls.append(float(recall))
        precisions.append(float(precision))
        f1s.append(float(f1))
        # keep the tailing zeros
        recalls_keep.append(recall)
        precisions_keep.append(precision)
        f1s_keep.append(f1)

    summaries = [match, exact_match, dists, recalls, precisions, f1s]
    num_rates = [match_num_rate, exact_match_num_rate]
    recall_set = [recalls_keep, precisions_keep, f1s_keep]
    return summaries, num_rates, recall_set


def generate_table(data, caption, label, tex_file):
    row_names = ["Overlapping", "Exact matches", "Char. dist. of partial overlaps", "Recall", "Precision", "F1-score"]
    col_names = ["", "diff\\textsubscript{line}", "diff\\textsubscript{word}", "\\name{}"]

    latex_table = "\\begin{table}[t]\n\\centering\n\\footnotesize\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{@{}" + "l" + "".join(["r"] * len(col_names)) + "@{}}\n"
    latex_table += "\\hline\n"

    latex_table += " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each row
    summaries = get_main_table_contents_util(data)
    for i, row_data in enumerate(summaries):
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table}"

    with open(tex_file, "w") as f:
        f.write(latex_table + "\n")

def annotated_data_main(common_folder, output_dir):
    # annotated data
    common = join(common_folder, "annodata")
    file_name_base = "measurement_results_metrics_annodata"
    file_list = [
            join(common, f"{file_name_base}_line.csv"),
            join(common, f"{file_name_base}_word.csv"),
            join(common, f"{file_name_base}.csv")]
    data = get_data(file_list)
    caption = "Results on tracking manually annotated data"
    label = "results_on_annotated_data"
    makedirs(output_dir, exist_ok=True)
    tex_file = join(output_dir, "annodata_comparison_table.tex")

    generate_table(data, caption, label, tex_file)

def suppression_main(common_folder, output_dir):
    # suppression data
    common = join(common_folder, "suppression")
    file_name_base = "measurement_results_metrics_suppression"
    file_list = [
            join(common, f"{file_name_base}_line.csv"),
            join(common, f"{file_name_base}_word.csv"),
            join(common, f"{file_name_base}.csv")]
    data = get_data(file_list)
    caption = "Results on tracking Python suppressions"
    label = "results_on_suppression"
    makedirs(output_dir, exist_ok=True)
    tex_file = join(output_dir, "suppression_comparison_table.tex")

    generate_table(data, caption, label, tex_file)


if __name__=="__main__":
    common_folder = join("data", "results", "measurement_results")
    output_dir = join("data", "results", "table_plots")
    annotated_data_main(common_folder, output_dir)
    suppression_main(common_folder, output_dir)