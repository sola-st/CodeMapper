from os import makedirs
from os.path import join
from anything_tracker.visualization.TableAnnoSuppressionResults import get_data, get_main_table_contents_util


def generate_table(data, caption, label, tex_file, context_lines):
    row_names = ["Overlapping", "Exact matches", "Char. dist. of partial overlaps", "Recall", "Precision", "F1-score"]
    col_names = [""]
    for num in context_lines:
        col_names.append(f"{num} lines")

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

def main(dataset, common_folder, output_dir, default_context_line, context_lines):
    common = join(common_folder, dataset)
    file_base = join(common, f"measurement_results_metrics_{dataset}")
    file_list = []
    for context_line in context_lines:
        if context_line == default_context_line:
            file_list.append(f"{file_base}.csv")
        elif context_line == 0:
            file_list.append(f"{file_base}_off_context.csv")
        else:
            file_list.append(f"{file_base}_{context_line}.csv")
    data = get_data(file_list)

    caption = None
    if dataset == "suppression":
        caption = "\\name{} with different context sizes (Suppression study data)."
    elif dataset == "annotation_a":
        caption = "\\name{} with different context sizes (Annotated data A)."
    else:
        caption = "\\name{} with different context sizes (Annotated data B)."
    label = f"context_sizes_{dataset}"
    makedirs(output_dir, exist_ok=True)
    tex_file = join(output_dir, f"context_size_comparison_table_{dataset}.tex")
    generate_table(data, caption, label, tex_file, context_lines)


if __name__=="__main__":
    common_folder = join("data", "results", "measurement_results")
    output_dir = join("data", "results", "table_plots")
    default_context_line = 15
    context_lines = [0, 1, 2, 3, 5, 10, 15, 20, 25, 30]

    main("annotation_a", common_folder, output_dir, default_context_line, context_lines)
    main("annotation_b", common_folder, output_dir, default_context_line, context_lines)
    main("suppression", common_folder, output_dir, default_context_line, context_lines)