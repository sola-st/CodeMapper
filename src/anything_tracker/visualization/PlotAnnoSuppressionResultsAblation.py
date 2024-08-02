import csv
from os import makedirs
from os.path import join
from matplotlib import pyplot as plt, rc
import numpy as np


def get_data(file_list):
    recall_set_to_numbers = [] # to dispaly the plot
    recall_set_keep = [] # to keep the tailing zeros after numbers, 

    for file in file_list:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            summary_line = line_list[-1][7:]
        # summary should be [YMW, pre character distance, post, all, recall, precision, f1, note]
        summary = [s for s in summary_line if s] 
        # recall, precision, f1 = summary[2: 5] 
        recall_set = summary[2: 5] 
        to_numbers = [float(n) for n in recall_set] # the float() will truncate the tailing zeros
        recall_set_to_numbers.append(to_numbers)
        recall_set_keep.append(recall_set)
    return recall_set_to_numbers #, recall_set_keep

def plot_recall_sets(data, xticklabels, plot_pdf):
    # Extract recall, precision, and f1-scores
    recall = [d[0] for d in data]
    precision = [d[1] for d in data]
    f1_score = [d[2] for d in data]

    n_sets = len(data)
    ind = np.arange(n_sets)[::-1]*0.4  # Y locations for the groups
    width = 0.1  # Width of the bars

    plt.rcParams.update({'font.size': 11})
    fig, ax = plt.subplots(figsize=(6, 4))

    rects1 = ax.barh(ind + width, recall, width, label='Recall', color='skyblue')
    rects2 = ax.barh(ind, precision, width, label='Precision', color='darkseagreen')
    rects3 = ax.barh(ind - width, f1_score, width, label='F1-score', color='lightsalmon')
    autolabel(ax, rects1)
    autolabel(ax, rects2)
    autolabel(ax, rects3)

    rc('axes')
    ax.set_yticks(ind)
    ax.set_yticklabels(xticklabels)
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1), prop={'size': 9})

    plt.tight_layout()
    plt.savefig(plot_pdf)


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

    def annotated_data_main(self):
        common_specific_folder = join(self.common_file_folder, "annodata")
        file_name_base = "measurement_results_metrics_annodata"

        file_list = []
        for suffix in self.file_suffies:
            file_list.append(join(common_specific_folder, f"{file_name_base}_{suffix}.csv"))
        file_list.append(join(common_specific_folder, f"{file_name_base}.csv")) # the one for AnythingTracker

        data = get_data(file_list)
        plot_pdf = join(output_dir, "annodata_ablation_plot.pdf")
        plot_recall_sets(data, xticklabels, plot_pdf)

    def suppression_main(self):
        common_specific_folder = join(self.common_file_folder, "suppression")
        file_name_base = "measurement_results_metrics_suppression"

        file_list = []
        for suffix in self.file_suffies:
            file_list.append(join(common_specific_folder, f"{file_name_base}_{suffix}.csv"))
        file_list.append(join(common_specific_folder, f"{file_name_base}.csv"))

        data = get_data(file_list)
        plot_pdf = join(output_dir, "suppression_ablation_plot.pdf")
        plot_recall_sets(data, xticklabels, plot_pdf)


if __name__=="__main__":
    file_suffies = ["off_diff",  "off_fine", "off_move", "off_search", "off_context"]
    common_file_folder = join("data", "results", "measurement_results")
    xticklabels = ["Disable diff-based\ncandidate extraction", 
                   "Disable candidate\nrefinement", 
                   "Disable movement\ndetection", 
                   "Disable text search", 
                   "Disable context-aware\nsimilarity",
                   "AnythingTracker"]
    output_dir = join("data", "results", "table_plots")
    makedirs(output_dir, exist_ok=True)
    init = PlotAnnoSuppressionResultsAblation(file_suffies, common_file_folder, xticklabels, output_dir)
    init.annotated_data_main()
    init.suppression_main()