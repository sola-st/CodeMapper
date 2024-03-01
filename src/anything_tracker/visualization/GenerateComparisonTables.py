import os
from os.path import join


def get_avg_numbers(filename):
    with open(filename, 'r') as file:
        data = file.readlines()[-1]
        data_splits = data.replace("\n", "").split(",")
        expect = [d for d in data_splits if d != ""]
    return expect

def generate_table(row_names, col_names, data, caption, label, tex_file, the_higher_the_better, add=False):
    latex_table = "\\begin{table}[htbp]\n\\centering\n"
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{" + "".join(["r"] * (len(col_names) + 1)) + "}\n"
    latex_table += "\\toprule\n"

    latex_table += "&" + " & ".join(col_names) + "\\\\\n"
    latex_table += "\\midrule\n"

    # To label the best performance, uodate data first
    col_num = len(data[0])
    textbf_loc_dict = {}
    for n in range(col_num):
        col_data = [float(sublist[n]) for sublist in data]
        if the_higher_the_better == True:
            textbf = max(col_data)
            textbf_row_idx = col_data.index(textbf)
        else:
            textbf = min(col_data)
            textbf_row_idx = col_data.index(textbf)

        if textbf_row_idx in textbf_loc_dict.keys():
            textbf_loc_dict[textbf_row_idx].update({n: textbf})
        else:
            textbf_loc_dict.update({
                textbf_row_idx : {
                    n: textbf
                    }
                })


    keys = textbf_loc_dict.keys()
    for i, row_data in enumerate(data):
        # list all the textbfs in current row
        if i in keys:
            textbfs = textbf_loc_dict[i]
            for col_idx, textbf in textbfs.items():
                row_data[col_idx] = "\\textbf{" + str(textbf) + "}"
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + "\\\\\n"

    latex_table += "\\bottomrule\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table}"

    write_mode = "w"
    if add == True:
        write_mode = "a"
    with open(tex_file, write_mode) as f:
        f.write(latex_table + "\n")

def main(line_git_diff_file, word_git_diff_file, anything_tracker_file, comparison_tex):
    data_a = get_avg_numbers(line_git_diff_file)
    data_b = get_avg_numbers(word_git_diff_file)
    data_c = get_avg_numbers(anything_tracker_file) 
    
    row_names = ['Line level git diff', 'Word level git diff', 'Our approach']

    dist_col_names = ['Pre-char dist', 'Post-char dist', "Character distance"]
    dist_data = [data_a[1:4], data_b[1:4], data_c[1:4]]
    dist_caption = "Comparison on Edit distance"
    the_higher_the_better = False
    generate_table(row_names, dist_col_names, dist_data, dist_caption, "comparison_avg_dist", comparison_tex, the_higher_the_better)

    recall_col_names = ["Recall", "Precision", "F1-score"]
    recall_data = [data_a[4:], data_b[4:], data_c[4:]]
    recall_caption = "Comparison on Performance"
    the_higher_the_better = True
    generate_table(row_names, recall_col_names, recall_data, recall_caption, "comparison_avg_recall", comparison_tex, the_higher_the_better, True)
    

if __name__=="__main__":
    results_folder = join("data", "results", "measurement_results")
    line_git_diff_file = join(results_folder, "measurement_results_anno38_gitline_v3_mean.csv")
    word_git_diff_file = join(results_folder, "measurement_results_anno38_gitword_v2_mean.csv")
    anything_tracker_file = join(results_folder, "measurement_results_anno38_combine_mean.csv")
    table_dir = join("data", "results", "table_plots")
    if not os.path.exists(table_dir):
        os.makedirs(table_dir)
    comparison_tex = join(table_dir, "table_example_combine.tex")
    main(line_git_diff_file, word_git_diff_file, anything_tracker_file, comparison_tex)