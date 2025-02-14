import csv
from itertools import zip_longest
import math
# from matplotlib import patches
import matplotlib.pyplot as plt
import numpy as np
from os.path import join

    
def get_detailed_execution_time(time_file):
    overall_time = []
    identify_target_file_time = []
    diff_computation_time = []
    iterate_hunk_time = [] # overlapping location check and easy-diff candi
    move_detection_time = []
    search_time = []
    # refine_range_time = []
    select_target_time = []

    with open(time_file, "r") as f:
        csv_reader = csv.reader(f)
        line_list = list(csv_reader)[1:]
        for line in line_list:
            if line:
                overall_time.append(float(line[4]) - float(line[7]))
                identify_target_file_time.append(float(line[6]))
                diff_computation_time.append(float(line[8]))
                # 9 overlapping+easy, 10 combination diff-base
                iterate_hunk_time.append(float(line[9])+ float(line[10]) + float(line[13]))
                move_detection_time.append(float(line[11]))
                search_time.append(float(line[12]))
                # refine_range_time.append(float(line[13]))
                select_target_time.append(float(line[3]))

        return overall_time, identify_target_file_time, diff_computation_time, \
                iterate_hunk_time, move_detection_time, search_time, select_target_time

def plot_detailed_times(groups, xticklabels, result_pdf):
    # Colors for each segment and the remaining part
    colors = ["#780C28", "#B3D8A8", "#F08080", "#FAC45A", "#7A70B5", "#C8AAAA"]
    # remaining_color = "#276C9E" 

    segment_labels = ['Identify target file', 'diff computation', 'Diff-Based Candidate Extraction', \
            'Movement Detection', 'Text Search', 'Target Region Selection']
    # remaining_label = 'Others'

    # Create the figure and axes
    plt.rcParams.update({'font.size': 14})
    fig, ax = plt.subplots()

    # Position of the bars on the x-axis
    bar_width = 0.4 
    group_positions = range(len(groups))
    # Create a handle for the remaining segment
    # remaining_patch = patches.Patch(color=remaining_color, label=remaining_label)

    # Loop over each group to plot
    for i, group in enumerate(groups):
        # overall = group['overall']
        subnumbers = group['subnumbers']
        # sum_subnumbers = sum(subnumbers)

        bottom = 0  # start position for the first segment in this group
        for j, (subnumber, color) in enumerate(zip(subnumbers, colors)):
            ax.bar(i, subnumber, width=bar_width, bottom=bottom, color=color, label=segment_labels[j] if i == 0 else "")
            bottom += subnumber

    # Plot the remaining part if there is any
    # if sum_subnumbers < overall:
    #     remaining = overall - sum_subnumbers
    #     ax.bar(i, remaining, width=bar_width, bottom=bottom, color=remaining_color, label=remaining_label if i == 0 else "")

    # Customize the plot
    ax.set_xticks(group_positions)
    ax.set_xticklabels(xticklabels)
    # ax.set_ylim(0, max(group['overall'] for group in groups) + 0.05)  # adjust y-axis limit
    max_overall = max(group['overall'] for group in groups)

    # Determine the number of decimal places in the max_overall to round to
    precision = -int(math.floor(math.log10(max_overall))) + 1
    increment = 10**-precision

    # Determine the new y-axis upper limit by rounding up
    new_ylim = math.ceil(max_overall / increment) * increment + 3 * increment

    # Set the y-axis limit on the actual plot
    ax.set_ylim(0, new_ylim)

    plt.ylabel('Execution time (milliseconds)')
    handles, labels = ax.get_legend_handles_labels()
    # Ensure the remaining label is in the legend even if not plotted
    # handles.append(remaining_patch)
    # labels.append(remaining_label)
    ax.legend(handles=handles, labels=labels)

    plt.tight_layout()
    plt.savefig(result_pdf)

def main():
    execution_time_folder = join("data", "results", "execution_time")
    xticklabels = [r'$\text{diff}_{\text{line}}$', r'$\text{diff}_{\text{word}}$', 'RegionTracker']
    result_pdf = join("data", "results", "table_plots", "execution_time_baseline_comparison_detailed_14_v2.pdf")
    data_type = ["annotation_a", "annotation_b", "suppression"] 

    file_list_annodata_a = []
    file_list_annodata_b = []
    file_list_suppression = []
    approaches = len(xticklabels)

    # colloct all execution time files
    for t in data_type:
        execution_time_file_line = join(execution_time_folder, t, f"execution_time_{t}_line.csv")
        execution_time_file_word = join(execution_time_folder, t, f"execution_time_{t}_word.csv")
        execution_time_file_at = join(execution_time_folder, t, f"execution_time_{t}.csv")
        if t == "annotation_a":
            file_list_annodata_a.append(execution_time_file_line)
            file_list_annodata_a.append(execution_time_file_word)
            file_list_annodata_a.append(execution_time_file_at)
        elif t == "annotation_b":
            file_list_annodata_b.append(execution_time_file_line)
            file_list_annodata_b.append(execution_time_file_word)
            file_list_annodata_b.append(execution_time_file_at)
        else:
            file_list_suppression.append(execution_time_file_line)
            file_list_suppression.append(execution_time_file_word)
            file_list_suppression.append(execution_time_file_at)
    
    groups = []
    for i, anno_file_a, anno_file_b, supp_file in zip_longest(range(approaches), file_list_annodata_a, file_list_annodata_b, file_list_suppression):
        overall_time, identify_target_file_time, diff_computation_time, iterate_hunk_time, move_detection_time, \
                search_time,  select_target_time = get_detailed_execution_time(anno_file_a)
        overall_time_b, identify_target_file_time_b, diff_computation_time_b, iterate_hunk_time_b, move_detection_time_b, \
                search_time_b,  select_target_time_b = get_detailed_execution_time(anno_file_b)
        overall_time_suppression, identify_target_file_time_suppression, diff_computation_time_suppression, \
                iterate_hunk_time_suppression, move_detection_time_suppression, search_time_suppression, \
                select_target_time_suppression = get_detailed_execution_time(supp_file)

        overall_time.extend(overall_time_b)
        identify_target_file_time.extend(identify_target_file_time_b)
        diff_computation_time.extend(diff_computation_time_b)
        iterate_hunk_time.extend(iterate_hunk_time_b)
        move_detection_time.extend(move_detection_time_b)
        search_time.extend(search_time_b)
        select_target_time.extend(select_target_time_b)

        overall_time.extend(overall_time_suppression)
        identify_target_file_time.extend(identify_target_file_time_suppression)
        diff_computation_time.extend(diff_computation_time_suppression)
        iterate_hunk_time.extend(iterate_hunk_time_suppression)
        move_detection_time.extend(move_detection_time_suppression)
        search_time.extend(search_time_suppression)
        select_target_time.extend(select_target_time_suppression)

        # compute the avg numbers
        overall_avg = np.average(overall_time)
        detailed_avgs = [np.average(identify_target_file_time), np.average(diff_computation_time), np.average(iterate_hunk_time), \
                         np.average(move_detection_time), np.average(search_time), np.average(select_target_time)]
        groups_item = {'overall': overall_avg, 'subnumbers': detailed_avgs}
        print(detailed_avgs)
        groups.append(groups_item)

    plot_detailed_times(groups, xticklabels, result_pdf)


if __name__=="__main__":
    main()
