import csv
import json
from os import makedirs
from os.path import join
from anything_tracker.visualization.TableAnnoSuppressionResults import get_main_table_contents_util


def get_data(file_list):
    '''
    To read the measurement results.
    The main difference with the "get_data in TableAnnoSuppressionResults.py"[1] is:
        * Simplify the summaries, e.g., not show exact numbers but remains only the rate.
    If need to show all the details, here can use the [1] instead.
    ''' 

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
                all -= 1
            else:
                summary_line = summary_line[7:]

        # summary should be [YMW, pre character distance, post, all, recall, precision, f1, note]
        summary = [s for s in summary_line if s] 
        match_results = json.loads(summary[0])
        e_matches = match_results["Y"]
        partial_overlaps = match_results["M"]
        overlappings = e_matches + partial_overlaps
        overlapping_rate = format((overlappings / all) * 100, digit)
        e_matches_rate = format((e_matches / all) * 100, digit)
        dist_results = json.loads(summary[1])
        dist = float(dist_results["dist"]["avg"])
        dists.append(dist)

        match.append(overlappings)
        match_num_rate.append(f"{overlapping_rate}\%")
        exact_match.append(e_matches)
        exact_match_num_rate.append(f"{e_matches_rate}\%")

        recall, precision, f1 = summary[2: 5] 
        # the float() will truncate the tailing zeros, but we need to compare the numbers
        recalls.append(float(recall))
        precisions.append(float(precision))
        f1s.append(float(f1))
        # keep the tailing zeros
        recalls_keep.append(recall)
        precisions_keep.append(precision)
        f1s_keep.append(f1)

    summaries = [match, exact_match, dists, recalls, precisions, f1s]
    only_rates = [match_num_rate, exact_match_num_rate]
    recall_set = [recalls_keep, precisions_keep, f1s_keep]
    return summaries, only_rates, recall_set

def generate_table(data, caption, label, tex_file):
    row_names = ["Overlapping", "Exact matches", "Char. dist.", "Recall", "Precision", "F1-score"]
    col_names = ["", "\\makecell{- diff\\\\extraction}", 
                 "\\makecell{- movement\\\\detection}", 
                 "\\makecell{- character\\\\searching}",
                 "\\makecell{- char.\\\\level}", 
                 "\\makecell{- context.\\\\similarity}",
                 "\\name{}"]

    latex_table = "\\begin{table}[t]\n\\centering\n\\begin{threeparttable}\n\\footnotesize\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\begin{tabular}{@{}" + "l" + "".join(["r"] * len(col_names)) + "@{}}\n"
    latex_table += "\\hline\n"

    latex_table += " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each column
    summaries = get_main_table_contents_util(data)
    for i, row_data in enumerate(summaries):
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    # start to add notes for tables
    # latex_table += "\\begin{tablenotes}[flushleft]\n\\footnotesize\n"
    # latex_table += "\\item Note: ``-'' means disabling the mentioned technique and Char. dist. indicates the average character distance of partial overlaps.\n"
    # latex_table += "\\end{tablenotes}\n"
    # latex_table += "\\end{threeparttable}\n"
    latex_table += "\\end{table}"

    with open(tex_file, "w") as f:
        f.write(latex_table + "\n")

def annotated_data_main(dataset, file_suffies, common_file_folder, output_dir):
    # annotated data
    common_specific_folder = join(common_file_folder, dataset)
    file_name_base = f"measurement_results_metrics_{dataset}"

    file_list = []
    for suffix in file_suffies:
        file_list.append(join(common_specific_folder, f"{file_name_base}_{suffix}.csv"))
    file_list.append(join(common_specific_folder, f"{file_name_base}.csv")) # the one for AnythingTracker

    data = get_data(file_list)
    caption = f"Disable partial techniques (Annotated data {dataset.split('_')[1].upper()})"
    label = f"ablation_on_{dataset}"
    tex_file = join(output_dir, f"{dataset}_ablation_table.tex")
    generate_table(data, caption, label, tex_file)

def suppression_main(file_suffies, common_file_folder, output_dir):
    # suppression data
    common_specific_folder = join(common_file_folder, "suppression")
    file_name_base = "measurement_results_metrics_suppression"

    file_list = []
    for suffix in file_suffies:
        file_list.append(join(common_specific_folder, f"{file_name_base}_{suffix}.csv"))
    file_list.append(join(common_specific_folder, f"{file_name_base}.csv"))

    data = get_data(file_list)
    caption = "Disable partial techniques (Python suppressions)"
    label = "ablation_on_suppression"
    tex_file = join(output_dir, "suppression_ablation_table.tex")
    generate_table(data, caption, label, tex_file)


if __name__=="__main__":
    file_suffies = ["off_diff", "off_move", "off_search", "off_fine", "off_context"]
    common_file_folder = join("data", "results", "measurement_results")
    output_dir = join("data", "results", "table_plots")
    makedirs(output_dir, exist_ok=True)
    annotated_data_main("annotation_a", file_suffies, common_file_folder, output_dir)
    annotated_data_main("annotation_b", file_suffies, common_file_folder, output_dir)
    suppression_main(file_suffies, common_file_folder, output_dir)