from os.path import join


def get_avg_numbers(filename):
    with open(filename, 'r') as file:
        data = file.readlines()[-1]
        data_splits = data.replace("\n", "").split(",")
        expect = [d for d in data_splits if d != ""]
    return expect

def generate_table(row_names, col_names, data, caption, label, tex_file):
    latex_table = "\\begin{table}[htbp]\n\\centering\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{" + "".join(["c"] * (len(col_names) + 1)) + "}\n"
    latex_table += "\\toprule\n"

    latex_table += "&" + " & ".join(col_names) + "\\\\\n"
    latex_table += "\\midrule\n"

    for i, row_data in enumerate(data):
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + "\\\\\n"

    latex_table += "\\bottomrule\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table}"

    with open(tex_file, "a") as f:
        f.write(latex_table + "\n")

def main(line_git_diff_file, word_git_diff_file, anything_tracker_file, comparison_tex):
    data_a = get_avg_numbers(word_git_diff_file)
    data_b = get_avg_numbers(line_git_diff_file)
    data_c = get_avg_numbers(anything_tracker_file) 

    row_names = ['Line level git diff', 'Word level git diff', 'Our approach']

    dist_col_names = ['Pre-edit distance', 'Post-edit distance', "Edit distance"]
    dist_data = [data_a[:3], data_b[:3], data_c[:3]]
    dist_caption = "Comparison on Edit distance"
    generate_table(row_names, dist_col_names, dist_data, dist_caption, "comparison_avg_dist", comparison_tex)

    recall_col_names = ["Recall", "Precision", "F1-score"]
    recall_data = [data_a[3:], data_b[3:], data_c[3:]]
    recall_caption = "Comparison on Performance"
    generate_table(row_names, recall_col_names, recall_data, recall_caption, "comparison_avg_recall", comparison_tex)
    

if __name__=="__main__":
    results_folder = "data/results"
    line_git_diff_file = join(results_folder, "measurement_results_anno38_gitline.csv")
    word_git_diff_file = join(results_folder, "measurement_results_anno38_gitword.csv")
    anything_tracker_file = join(results_folder, "measurement_results_anno38.csv")
    comparison_tex = join(results_folder, "table_plots", "table_example.tex")
    main(line_git_diff_file, word_git_diff_file, anything_tracker_file, comparison_tex)
