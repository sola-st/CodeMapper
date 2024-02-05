import csv
import matplotlib.pyplot as plt
from os.path import join

import numpy as np

def read_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        overall_distance_index = header.index('Overall distance')
        data = [int(row[overall_distance_index]) for row in reader]
    return data

def main(anything_tracker_file, line_git_diff_file, word_git_diff_file, comparison_pdf):
    data_a = read_csv(anything_tracker_file)
    data_b = read_csv(line_git_diff_file)
    data_c = read_csv(word_git_diff_file)

    fig, ax = plt.subplots()

    ax.scatter(data_a, range(len(data_a)), color='green', label='AnythingTracker')
    ax.scatter(data_b, range(len(data_b)), color='purple', label='Line level git diff')
    ax.scatter(data_c, range(len(data_c)), color='orange', label='Word level git diff')

    our_max_dist = max(data_a)
    our_max_dist_closer = ((our_max_dist + 49) // 50) * 50
    x_ticks_dense = np.arange(0, our_max_dist_closer + 1, 50)
    max_dist = max(our_max_dist, max(data_b), max(data_c))
    max_dist_closer = ((max_dist + 99) // 100) * 100
    x_ticks_sparse = np.arange(our_max_dist_closer, max_dist_closer + 1, 100)
    x_ticks = np.concatenate((x_ticks_dense, x_ticks_sparse))

    ax.set_xticks(x_ticks)

    ax.set_title('Scatter Plot of Edit Distance')
    ax.set_xlabel('Edit Distance')  # (-1: Bad quality)
    ax.set_ylabel('Data Point Index')
    ax.legend(['AnythingTracker', 'Line level git diff', 'Word level git diff'])

    total_range = max_dist + 1
    total_ticks = len(x_ticks)
    pixels_per_tick = 10  # Adjust as needed
    fig_width = total_range / total_ticks * pixels_per_tick
    fig.set_size_inches(fig_width / 100, 6)  # Convert inches to pixels

    plt.tight_layout()
    plt.savefig(comparison_pdf)

if __name__=="__main__":
    results_folder = "data/results"
    anything_tracker_file = join(results_folder, "measurement_results_anno38_v1_updated.csv")
    line_git_diff_file = join(results_folder, "measurement_results_anno38_gitline_v2.csv")
    word_git_diff_file = join(results_folder, "measurement_results_anno38_gitword_v1.csv")
    comparison_pdf = join(results_folder, "table_plots", "example_1.pdf")
    main(anything_tracker_file, line_git_diff_file, word_git_diff_file, comparison_pdf)

