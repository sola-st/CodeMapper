import matplotlib.pyplot as plt
from os.path import join

import numpy as np
from pandas import read_csv

def get_data(filename):
    data = read_csv(filename)

    dists = data['Character distance'].tolist()[:-1]
    recalls = data['Recall'].tolist()[:-1]
    precisions = data['Precision'].tolist()[:-1]
    f1s = data['F1-score'].tolist()[:-1]

    return dists, recalls, precisions, f1s

def generate_plots(data_a, data_b, data_c, ylabel, comparison_pdf):
    font_size = 10
    fig, ax = plt.subplots(figsize=(10, 6))

    bar_width = 0.6

    bar_positions = np.arange(len(data_a)) * 5
    ax.bar(bar_positions, data_a, width=bar_width, color='orange', label='Line level git diff')
    ax.bar(bar_positions + bar_width, data_b, width=bar_width, color='purple', label='Word level git diff')
    ax.bar(bar_positions + 2 * bar_width, data_c, width=bar_width, color='green', label='AnythingTracker')

    ax.set_xticks(bar_positions + bar_width)
    ax.set_xticklabels(range(len(data_a)), fontsize=font_size)

    ax.set_xlabel('Data Point', fontsize =font_size+2)
    ax.set_ylabel(ylabel, fontsize =font_size+2)
    ax.legend()

    plt.tight_layout()
    plt.savefig(comparison_pdf)

def main(anything_tracker_file, line_git_diff_file, word_git_diff_file, comparison_pdf):
    dists_a, recalls_a, precisions_a, f1s_a = get_data(line_git_diff_file)
    dists_b, recalls_b, precisions_b, f1s_b = get_data(word_git_diff_file)
    dists_c, recalls_c, precisions_c, f1s_c = get_data(anything_tracker_file) 

    generate_plots(dists_a, dists_b, dists_c, 'Character Distance', comparison_pdf.replace(".pdf", "_dist.pdf"))
    generate_plots(recalls_a, recalls_b, recalls_c, 'Recall', comparison_pdf.replace(".pdf", "_recall.pdf"))
    generate_plots(precisions_a, precisions_b, precisions_c, 'Precision', comparison_pdf.replace(".pdf", "_pre.pdf"))
    generate_plots(f1s_a, f1s_b, f1s_c, 'F1-score', comparison_pdf.replace(".pdf", "_f1.pdf"))

if __name__=="__main__":
    results_folder = "data/results"
    line_git_diff_file = join(results_folder, "measurement_results_anno38_gitline_v3_mean.csv")
    word_git_diff_file = join(results_folder, "measurement_results_anno38_gitword_v2_mean.csv")
    anything_tracker_file = join(results_folder, "measurement_results_anno38_combine_mean.csv")
    comparison_pdf = join(results_folder, "table_plots", "example_bar_plot.pdf")
    main(anything_tracker_file, line_git_diff_file, word_git_diff_file, comparison_pdf)

