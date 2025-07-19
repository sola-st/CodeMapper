import csv
from os import makedirs
from os.path import join, exists
from matplotlib import pyplot as plt, rc
import numpy as np


def get_data(file_list):
    recall_set_to_numbers = [] # to dispaly the plot
    recall_set_keep = [] # to keep the tailing zeros after numbers, 

    for file in file_list:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            # summary_line = line_list[-2][7:]
            summary_line = line_list[-1]
            tmp = [s for s in summary_line if s]
            if len(tmp) < 2:
                summary_line = line_list[-2]
            summary_line = summary_line[7:]
        # summary should be [YMW, pre character distance, post, all, recall, precision, f1, note]
        summary = [s for s in summary_line if s] 
        # recall, precision, f1 = summary[2: 5] 
        recall_set = summary[2: 5] 
        to_numbers = [float(n) for n in recall_set] # the float() will truncate the tailing zeros
        recall_set_to_numbers.append(to_numbers)
        recall_set_keep.append(recall_set)
    return recall_set_to_numbers #, recall_set_keep

def plot_recall_sets_single_plot(data, xticklabels, plot_pdf):
    # Extract recall, precision, and f1-scores
    recall = [d[0] for d in data]
    precision = [d[1] for d in data]
    f1_score = [d[2] for d in data]

    n_sets = len(data)
    ind = np.arange(n_sets)[::-1]*0.4  # Y locations for the groups
    width = 0.1  # Width of the bars

    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams.update({'font.size': 10})
    fig, ax = plt.subplots(figsize=(4, 3))

    rects1 = ax.barh(ind + width, recall, width, label='Recall', color='skyblue')
    rects2 = ax.barh(ind, precision, width, label='Precision', color='darkseagreen')
    rects3 = ax.barh(ind - width, f1_score, width, label='F1-score', color='lightsalmon')
    autolabel(ax, rects1)
    autolabel(ax, rects2)
    autolabel(ax, rects3)

    rc('axes')
    ax.set_yticks(ind)
    ax.set_yticklabels(xticklabels)
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1), prop={'size': 10})

    plt.tight_layout(pad=0)
    plt.savefig(plot_pdf)

def plot_recall_sets_sub_plot(ax, data, xticklabels, title, show_yticks):
    # Extract recall, precision, and f1-scores
    recall = [d[0] for d in data]
    precision = [d[1] for d in data]
    f1_score = [d[2] for d in data]

    n_sets = len(data)
    ind = np.arange(n_sets)[::-1] * 0.4  # Y locations for the groups
    width = 0.1  # Width of the bars

    rects1 = ax.barh(ind + width, recall, width, label='Recall', color='skyblue')
    rects2 = ax.barh(ind, precision, width, label='Precision', color='darkseagreen')
    rects3 = ax.barh(ind - width, f1_score, width, label='F1-score', color='lightsalmon')
    autolabel(ax, rects1)
    autolabel(ax, rects2)
    autolabel(ax, rects3)

    # Only show y-tick labels for the first subplot
    if show_yticks:
        ax.set_yticks(ind)
        ax.set_yticklabels(xticklabels)
        ax.legend(loc='upper right', prop={'size': 9})
    else:
        ax.set_yticks(ind)
        ax.set_yticklabels([])

    ax.set_title(title)
    

def plot_all_recall_sets(datasets, xticklabels, titles, output_pdf):
    plt.rcParams["pdf.fonttype"] = 42
    fig, axes = plt.subplots(1, len(datasets), figsize=(12, 4), sharey=True)  # Share Y-axis labels

    for i, (data, title) in enumerate(zip(datasets, titles)):
        plot_recall_sets_sub_plot(axes[i], data, xticklabels, title, show_yticks=(i == 3))  # Show y-labels only once

    plt.tight_layout()
    plt.savefig(output_pdf)


def autolabel(ax, rects):
    # Attach a text label inside each bar in `rects`, aligned to the right end of the bar.
    for rect in rects:
        width = rect.get_width()
        ax.text(
            width - 0.1,                      # X position: width of the bar minus a small offset
            rect.get_y() + rect.get_height() / 2,  # Y position: center of the bar
            f'{width:.3f}',                   # Text to display: formatted to 2 decimal places
            ha='right',                       # Horizontal alignment: right
            va='center',                      # Vertical alignment: center
            color='white',                    # Text color
            fontsize=10                       # Font size
        )

class PlotAnnoSuppressionResultsAblation():
    def __init__(self, file_suffies, common_file_folder, xticklabels, output_dir):
        self.file_suffies = file_suffies
        self.common_file_folder = common_file_folder
        self.xticklabels = xticklabels
        self.output_dir = output_dir

    def run(self, datasets, overall_plot=True):
        merged_data = []
        for dataset in datasets:
            common_specific_folder = join(self.common_file_folder, dataset)
            file_name_base = f"measurement_results_metrics_{dataset}"

            file_list = []
            for suffix in self.file_suffies:
                file = join(common_specific_folder, f"{file_name_base}_{suffix}.csv")
                if suffix == "off_context" and not exists(file):
                    file = join(common_specific_folder, f"{file_name_base}_0.csv")
                file_list.append(file)
            file_list.append(join(common_specific_folder, f"{file_name_base}.csv")) # the one for our approach

            data = get_data(file_list)
            merged_data.append(data)

        if len(datasets) > 1:
            avg = [
                [
                    sum(values) / len(values)
                    for values in zip(*rows)
                ]
                for rows in zip(*merged_data)
            ]
            data = avg

        if overall_plot:
            return data
        else:
            plot_pdf = join(output_dir, f"{dataset}_ablation_plot.pdf")
            plot_recall_sets_single_plot(data, xticklabels, plot_pdf)


if __name__=="__main__":
    '''
    Three options for visualizing ablation study results:
     1. generate a single plot for each dataset
     2. generate an overall plot for all datasets
     3. Genrate an overall plot for the four datasets
    '''
    option = 3

    file_suffies = ["off_diff",  "off_fine", "off_move", "off_search", "off_context"]
    common_file_folder = join("data", "results", "measurement_results")
    xticklabels = ["Disable diff-based\ncandidate extraction", 
                   "Disable candidate\nrefinement", 
                   "Disable movement\ndetection", 
                   "Disable text search", 
                   "Disable context-aware\nsimilarity",
                   "CodeMapper"]
    output_dir = join("data", "results", "table_plots")
    makedirs(output_dir, exist_ok=True)
    init = PlotAnnoSuppressionResultsAblation(file_suffies, common_file_folder, xticklabels, output_dir)

    if option == 1:
        init.run("annotation_a", False)
        init.run("annotation_b", False)
        init.run("suppression", False)
        print("Plot generation done.")
    elif option == 2:
        annodata_a = init.run("annotation_a", True)
        annodata_b = init.run("annotation_b", True)
        suppression_data = init.run("suppression", True)
        data = [annodata_a, annodata_b, suppression_data]
        plot_pdf = join(output_dir, "overall_ablation_plot.pdf")
        titles = ["Data A", "Data B", "Suppression study data"]
        plot_all_recall_sets(data, xticklabels, titles, plot_pdf)

        variable = init.run("variable_test", True)
        block = init.run("block_test", True)
        method = init.run("method_test", True)
        data = [variable, block, method]
        plot_pdf = join(output_dir, "overall_ablation_plot_codetracker_data.pdf")
        titles = ["Variable", "Block", "Method"]
        plot_all_recall_sets(data, xticklabels, titles, plot_pdf)
    else:
        annodata_a = init.run(["annotation_a"], True)
        annodata_b = init.run(["annotation_b"], True)
        suppression_data = init.run(["suppression"], True)
        merged = init.run(["variable_test", "block_test", "method_test"], True)
        data = [annodata_a, annodata_b, suppression_data, merged]
        plot_pdf = join(output_dir, "overall_ablation_plot_merged.pdf")
        titles = ["Data A", "Data B", "Suppression study data", "CodeTracker data"]
        plot_all_recall_sets(data, xticklabels, titles, plot_pdf)


