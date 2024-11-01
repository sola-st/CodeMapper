from os.path import join
from matplotlib import pyplot as plt
import numpy as np
from anything_tracker.visualization.PlotExexutionTimeComparison import get_execution_time


def plot_comparison(xticklabels, overall_data, result_pdf):
    plt.rcParams.update({'font.size': 12})
    fig, ax = plt.subplots(figsize=(15, 5)) 
    # Create box plots for each group
    ax.boxplot(overall_data, patch_artist=True)

    # Set labels and title
    ax.set_xticklabels(xticklabels)
    ax.set_ylabel('Execution time (seconds)')

    medians = []
    means = []
    for data in overall_data:
        medians.append(np.median(data))
        means.append(np.mean(data))

    # Add text annotations for median and mean values
    for i, (median, mean) in enumerate(zip(medians, means)):
        ax.text(i + 1, median, f'Median: {median:.3f}', ha='center', va='center')
        ax.text(i + 1, mean * 2, f'Avg: {mean:.3f}', ha='center', va='center')
    
    plt.tight_layout(pad=0)
    plt.savefig(result_pdf)

def main_context_size_comparison(context_lines, default_context_line, result_pdf):
    execution_time_folder = join("data", "results", "execution_time")
    xticklabels = []
    for num in context_lines:
        xticklabels.append(f"{num} lines")
    data_type = ["annodata", "suppression"]

    file_list_annodata = []
    file_list_suppression = []
    approaches = len(xticklabels)
    overall_data = []

    # colloct all execution time files
    for i, t in enumerate(data_type):
        for c in context_lines:
            execution_time_file = join(execution_time_folder, t, f"execution_time_{t}.csv")
            if c != default_context_line:
                execution_time_file = execution_time_file.replace(".csv", f"_{c}.csv")

            if i == 0:
                file_list_annodata.append(execution_time_file)
            else:
                file_list_suppression.append(execution_time_file)

    for i, anno_file, supp_file in zip(range(approaches), file_list_annodata, file_list_suppression):
        time = []
        time = get_execution_time(anno_file)
        supp_time = get_execution_time(supp_file)
        time.extend(supp_time)
        overall_data.append(time)

    plot_comparison(xticklabels, overall_data, result_pdf)


if __name__=="__main__":
    # Option 1. compare with baselines
    context_lines = [0, 1, 2, 3, 5, 10, 15, 20, 25, 30]
    default_context_line = 15
    result_pdf = join("data", "results", "table_plots", "execution_time_context_sizes.pdf")
    main_context_size_comparison(context_lines, default_context_line, result_pdf)