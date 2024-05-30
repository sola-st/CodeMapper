import csv
import json

def get_data(file_list):
    summaries = []

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
        matches_rate = round((matches / all) * 100, 1)
        overlaps_rate = round((overlaps / all) * 100, 1)
        nonoverlaps_rate = round((nonoverlaps / all) * 100, 1)

        dist_results = json.loads(summary[1])
        pre = dist_results["pre_dist"]["avg"]
        post = dist_results["post_dist"]["avg"]
        dist = dist_results["dist"]["avg"]

        recall, presicion, f1 = summary[2: 5] 

        formamtted_summary = [matches_rate, overlaps_rate, nonoverlaps_rate, recall, presicion, f1, pre, post, dist]
        summaries.append(formamtted_summary)
    return summaries


def generate_table(row_names, col_names, data, caption, label, tex_file, the_higher_the_better, add=False):
    latex_table = "\\begin{table*}[htbp]\n\\centering\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{" + "l" + "".join(["r"] * len(col_names)) + "}\n"
    latex_table += "\\hline\n"

    latex_table += " & " + " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each column
    col_num = len(data[0])
    textbf_loc_dict = {}
    for n in range(col_num):
        col_data = [float(sublist[n]) for sublist in data]
        if the_higher_the_better[n]:
            textbf = max(col_data)
        else:
            textbf = min(col_data)

        for row_idx, value in enumerate(col_data):
            if value == textbf:
                if row_idx in textbf_loc_dict:
                    textbf_loc_dict[row_idx].append(n)
                else:
                    textbf_loc_dict[row_idx] = [n]

    for i, row_data in enumerate(data):
        for j in range(3): # to display the % percent
            row_data[j] = f"{row_data[j]}\%"
        if i in textbf_loc_dict:
            for col_idx in textbf_loc_dict[i]:
                row_data[col_idx] = "\\textbf{" + str(row_data[col_idx]) + "}"
                # if col_idx < 3: # to display the % percent
                #     row_data[col_idx] = "\\textbf{" + f"{str(row_data[col_idx])}\%" + "}"
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table*}"

    write_mode = "w"
    if add:
        write_mode = "a"
    with open(tex_file, write_mode) as f:
        f.write(latex_table + "\n")

# suppression data
row_names = ["Line level diff", "Character level diff", "AnythingTracker"] # , "Suppression C"
col_names = ["Exact matches", "Overlaps", "Nonoverlaps", "Precision", "Recall", "F1-score", "Pre-Chardist", "Post-Chardist", "Chardist"]
file_list = [
             "data/results/measurement_results/latest/measurement_results_metrics_suppression_line_level.csv",
             "data/results/measurement_results/latest/measurement_results_metrics_suppression_character_level.csv",
             "data/results/measurement_results/latest/measurement_results_metrics_suppression.csv"]
data = get_data(file_list)
caption = "Performance on tracking Python Suppression"
label = "performance_on_suppression"
tex_file = "table.tex"
the_higher_the_better = [True, False, False, True, True, True, False, False, False]

generate_table(row_names, col_names, data, caption, label, tex_file, the_higher_the_better)
