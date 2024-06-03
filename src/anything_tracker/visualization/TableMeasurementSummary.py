import csv
import json

def get_data(file_list):
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

    for file in file_list:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            summary_line = list(csv_reader)[-1]

        # summary should be [YMW, pre character distance, post, all, recall, presicion, f1, note]
        summary = [s for s in summary_line if s] 
        match_results = json.loads(summary[0])
        matches = match_results["Y"]
        overlaps = match_results["M"]
        nonoverlaps = match_results["W"]
        all = matches + overlaps + nonoverlaps
        matches_rate = format((matches / all) * 100, digit)
        overlaps_rate = format((overlaps / all) * 100, digit)

        dist_results = json.loads(summary[1])
        dist = float(dist_results["dist"]["avg"])

        recall, presicion, f1 = summary[2: 5] 

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


def generate_table(row_names, col_names, data, caption, label, tex_file, the_higher_the_better):
    latex_table = "\\begin{table*}[htbp]\n\\centering\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{" + "l" + "".join(["r"] * len(col_names)) + "}\n"
    latex_table += "\\hline\n"

    latex_table += " & " + " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each column
    split_num = 6
    data_numbers = data[:split_num]
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
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table*}"

    with open(tex_file, "w") as f:
        f.write(latex_table + "\n")

# suppression data
row_names = ["Line level diff", "Character level diff", "AnythingTracker"]
col_names = ["Exact matches", "Overlapping", "Recall", "Precision", "F1-score", "Character distance"]
file_list = [
             "data/results/measurement_results/annotation/measurement_results_metrics_anno_line_0603.csv",
             "data/results/measurement_results/annotation/measurement_results_metrics_anno_character_0603.csv",
             "data/results/measurement_results/annotation/measurement_results_metrics_anno_update.csv"]
data = get_data(file_list)
caption = "Performance on tracking annotated data"
label = "performance_on_annotated_data"
tex_file = "data/results/table_plots/annodata_comparison_table.tex"
the_higher_the_better = [True, False, True, True, True, False]

generate_table(row_names, col_names, data, caption, label, tex_file, the_higher_the_better)
