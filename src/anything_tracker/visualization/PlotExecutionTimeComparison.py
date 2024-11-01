import csv
import matplotlib.pyplot as plt
import numpy as np
from os.path import join


def get_execution_time(time_file, individual_times=False):
    with open(time_file, "r") as f:
        csv_reader = csv.reader(f)
        line_list = list(csv_reader)[1:]
    if individual_times == True:
        times_1 = [float(line[2]) for line in line_list if line]
        times_2 = [float(line[3]) for line in line_list if line]
        return times_1, times_2
    else:
        overall_time = [float(line[4]) for line in line_list if line]
        return overall_time

def plot_comparison(xticklabels, overall_data, result_pdf): # [line_data, word_data, anythingtracker_data]
    plt.rcParams.update({'font.size': 12})
    fig, ax = plt.subplots(figsize=(6, 3))
    # Create box plots for each group
    ax.boxplot(overall_data, patch_artist=True)

    # Set labels and title
    ax.set_xticklabels(xticklabels)
    ax.set_ylabel('Execution time (seconds)')

    line_data, word_data, at_data = overall_data
    medians = [np.median(line_data), np.median(word_data), np.median(at_data)]
    means = [np.mean(line_data), np.mean(word_data), np.mean(at_data)]

    # Add text annotations for median and mean values
    for i, (median, mean) in enumerate(zip(medians, means)):
        ax.text(i + 1, 4, f'Median: {median:.3f}', ha='center', va='center')
                 # bbox=dict(facecolor='white', edgecolor='black'))
        ax.text(i + 1, 5, f'Avg: {mean:.3f}', ha='center', va='center')
                # bbox=dict(facecolor='yellow', edgecolor='black'))
    
    plt.tight_layout(pad=0)
    plt.savefig(result_pdf)

def plot_comparison_violin(xticklabels, overall_data, result_pdf):
    fig, ax = plt.subplots()
    parts = ax.violinplot(overall_data, showmeans=True, showmedians=True)

    ax.set_xticks(np.arange(1, len(xticklabels) + 1))
    ax.set_xticklabels(xticklabels, fontsize=12)
    ax.set_ylabel('Execution time (seconds)', fontsize=12)

    line_data, word_data, at_data = overall_data
    medians = [np.median(line_data), np.median(word_data), np.median(at_data)]
    means = [np.mean(line_data), np.mean(word_data), np.mean(at_data)]
    # Add text annotations for median values
    for i, (median, mean) in enumerate(zip(medians, means)):
        ax.text(i + 1, median, f'Median: {median:.3f}', ha='center', va='center')
        ax.text(i + 1, mean * 2, f'Avg: {mean:.3f}', ha='center', va='center') 

    # Customize the violin plot appearance
    for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):
        vp = parts[partname]
        vp.set_edgecolor('black')
        vp.set_linewidth(1)

    for pc in parts['bodies']:
        pc.set_facecolor('lightblue')
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)

    plt.savefig(result_pdf)

def main_baseline_comparison():
    execution_time_folder = join("data", "results", "execution_time")
    xticklabels = [r'$\text{diff}_{\text{line}}$', r'$\text{diff}_{\text{word}}$', 'AnythingTracker']
    result_pdf = join("data", "results", "table_plots", "execution_time_baseline_comparison.pdf")
    data_type = ["annodata", "suppression"]

    file_list_annodata = []
    file_list_suppression = []
    approaches = len(xticklabels)
    overall_data = []

    # colloct all execution time files
    for i, t in enumerate(data_type):
        execution_time_file_line = join(execution_time_folder, t, f"execution_time_{t}_line.csv")
        execution_time_file_word = join(execution_time_folder, t, f"execution_time_{t}_word.csv")
        execution_time_file_at = join(execution_time_folder, t, f"execution_time_{t}.csv")
        if i == 0:
            file_list_annodata.append(execution_time_file_line)
            file_list_annodata.append(execution_time_file_word)
            file_list_annodata.append(execution_time_file_at)
        else:
            file_list_suppression.append(execution_time_file_line)
            file_list_suppression.append(execution_time_file_word)
            file_list_suppression.append(execution_time_file_at)
    
    for i, anno_file, supp_file in zip(range(approaches), file_list_annodata, file_list_suppression):
        time = []
        time = get_execution_time(anno_file)
        supp_time = get_execution_time(supp_file)
        time.extend(supp_time)
        overall_data.append(time)

    plot_comparison(xticklabels, overall_data, result_pdf)

def main_anythingtracker():
    execution_time_folder = join("data", "results", "execution_time")
    xlabels = ["AT-Phase1", "AT-Phase2", "AT"]
    result_pdf = join("data", "results", "table_plots", "execution_time_anythingtracker.pdf")

    # colloct all execution time files
    anno_file = join(execution_time_folder, "annodata", "execution_time_annodata.csv")
    supp_file = join(execution_time_folder, "suppression", "execution_time_suppression.csv")
    all = []
    all_phase1 = []
    all_phase2 = []
    anno_time = get_execution_time(anno_file)
    anno_1, anno_2 = get_execution_time(anno_file, True)
    supp_time = get_execution_time(supp_file)
    supp_1, supp_2 = get_execution_time(supp_file, True)

    # overall time
    all.extend(anno_time)
    all.extend(supp_time)

    # overall 1
    all_phase1.extend(anno_1)
    all_phase1.extend(supp_1)

    # overall 2
    all_phase2.extend(anno_2)
    all_phase2.extend(supp_2)
    
    plot_comparison(xlabels, [all_phase1, all_phase2, all], result_pdf)


if __name__=="__main__":
    # Option 1. compare with baselines
    main_baseline_comparison()

    # Option 2. exexcution time details for AnythingTracker
    main_anythingtracker()