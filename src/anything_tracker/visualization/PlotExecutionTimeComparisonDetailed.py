import csv
from itertools import zip_longest
import json
import math
from matplotlib import patches
import matplotlib.pyplot as plt
import numpy as np
from os.path import join


def plot_detailed_times_record_ratios(groups, xticklabels, result_pdf):
    all_ratios = []
    # Colors for each segment
    colors = ["#B3D8A8", "#780C28", "#FAC45A", "#F08080", "#7A70B5", "#C8AAAA"]
    segment_labels = ['Identify target file', 'diff computation', 'Diff-Based Candidate Extraction',
                      'Movement Detection', 'Text Search', 'Target Region Selection']
    context_size_info = ["5 lines", "10 lines", "15 lines (Default)"]

    # Create the figure and axes
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams.update({'font.size': 12})
    fig, ax = plt.subplots(figsize=(6, 4))
    
    num_groups = len(groups)
    group_last_n = 3  # Last three bars will be grouped under one label
    bar_width = 0.4  # Width of bars

    # Define positions: normal spacing for first ones, closer spacing for the last three
    group_positions_tmp = list(range(num_groups - group_last_n)) # Normal positions
    group_positions = [i *0.6 for i in group_positions_tmp]
    last_group_positions = np.linspace(num_groups - group_last_n, num_groups - group_last_n + 1, group_last_n)  # Closer spacing
    group_positions.extend(last_group_positions)

    # Set x-tick positions: Normal + Centered position for last three
    xtick_positions = list(range(num_groups - group_last_n)) + [np.mean(last_group_positions)]
    adjusted_xticklabels = xticklabels[:num_groups - group_last_n]
    adjusted_xticklabels.append(xticklabels[-1])  # One label for last 3

    # Plot bars
    for i, (group, approach) in enumerate(zip(groups, xticklabels)):
        ratios = {"Approach": approach}
        overall = group['overall']
        subnumbers = group['subnumbers']
        ratios.update({"Overall": f"{(overall):.4f}"})
        ratios.update({"Phase_1": f"{(overall - subnumbers[-1]):.4f}"})

        bottom = 0  
        # Determine x position for bar
        if i < num_groups - group_last_n:
            x_pos = i  # Normal positioning
        else:
            x_pos = last_group_positions[i - (num_groups - group_last_n)]  # Keep them individually placed

        # Plot each segment in the stacked bar
        for subnumber, color, substep in zip(group['subnumbers'], colors, segment_labels):
            ax.bar(x_pos, subnumber, width=bar_width, bottom=bottom, color=color)
            if i > 1 and bottom == 0: # 0 for line diff, 1 for word diff
                ax.text(x_pos, 20, f"{context_size_info[i-2]}", 
                        ha='center', va='bottom', color='black', rotation=90)

            bottom += subnumber
            # Compute ratio
            ratio = f"{(subnumber / overall * 100):.2f}%"  
            ratios.update({substep: f"{subnumber:.4f} ({ratio})"})
        all_ratios.append(ratios)

    # Set x-ticks (single label for last three bars)
    ax.set_xticks(xtick_positions)
    ax.set_xticklabels(adjusted_xticklabels)
    max_overall = max(group['overall'] for group in groups)
    # Determine the number of float places in the max_overall to round to
    precision = -int(math.floor(math.log10(max_overall))) + 1
    increment = 10**-precision

    # Determine the new y-axis upper limit by rounding up
    new_ylim = math.ceil(max_overall / increment) * increment + 4 * increment # a smaller y
    # new_ylim = math.ceil(max_overall*2 / increment) * increment # a much bigger y
    ax.set_ylim(0, new_ylim)


    # Labels and legend
    plt.ylabel('Execution time (milliseconds)')
    ax.legend(loc="upper left", 
              handles=[patches.Patch(color=color, label=label) for color, label in zip(colors, segment_labels)])

    plt.tight_layout()
    plt.savefig(result_pdf)


    ratio_record_file = result_pdf.replace(".pdf", "_ratios.json")
    with open(ratio_record_file, "w") as ds:
        json.dump(all_ratios, ds, indent=4, ensure_ascii=False)
    
class PlotExecutionTimeComparisonDetailed():
    def __init__(self, execution_time_folder, xticklabels, result_pdf, data_type):
        self.execution_time_folder = execution_time_folder
        self.xticklabels = xticklabels
        self.result_pdf = result_pdf
        self.data_type = data_type

        self.clear_time_records()
        
    def clear_time_records(self):
        self.overall_time = []
        self.identify_target_file_time = []
        self.diff_computation_time = []
        self.iterate_hunk_time = []
        self.move_detection_time = []
        self.search_time = []
        self.select_target_time = []

    def get_detailed_execution_time(self, time_file):
        overall_time = []
        identify_target_file_time = []
        diff_computation_time = []
        iterate_hunk_time = [] # overlapping location check and easy-diff candi
        move_detection_time = []
        search_time = []
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

        # return overall_time, identify_target_file_time, diff_computation_time, \
        #         iterate_hunk_time, move_detection_time, search_time, select_target_time

        # append these time records to the self.<..._time>
        self.overall_time.extend(overall_time)
        self.identify_target_file_time.extend(identify_target_file_time)
        self.diff_computation_time.extend(diff_computation_time)
        self.iterate_hunk_time.extend(iterate_hunk_time)
        self.move_detection_time.extend(move_detection_time)
        self.search_time.extend(search_time)
        self.select_target_time.extend(select_target_time)

    def run(self):
        file_lists = {
            "annotation_a": [],
            "annotation_b": [],
            "suppression": [],
            "variable_test": [],
            "block_test": [],
            "method_test": []
        }

        # Collect all execution time files
        for t in data_type:
            base_path = join(execution_time_folder, t)
            file_names = [
                f"execution_time_{t}_line.csv",
                f"execution_time_{t}_word.csv",
                f"execution_time_{t}_5.csv",
                f"execution_time_{t}_10.csv",
                f"execution_time_{t}.csv"
            ]
            full_paths = [join(base_path, name) for name in file_names]

            if t in file_lists:
                file_lists[t].extend(full_paths)

        groups = []
        for files in zip_longest(
            file_lists["annotation_a"],
            file_lists["annotation_b"],
            file_lists["suppression"],
            file_lists["variable_test"],
            file_lists["block_test"],
            file_lists["variable_test"]
        ):
            for f in files:
                self.get_detailed_execution_time(f)

            # compute the avg numbers
            detailed_avgs = [np.mean(self.identify_target_file_time), np.mean(self.diff_computation_time), \
                            np.mean(self.iterate_hunk_time), np.mean(self.move_detection_time), \
                            np.mean(self.search_time), np.mean(self.select_target_time)]
            overall_avg = sum(detailed_avgs) # avoid the tiny inaccuracy in the timer.
            groups_item = {'overall': overall_avg, 'subnumbers': detailed_avgs}
            groups.append(groups_item)
            print(groups_item)
            self.clear_time_records()

        plot_detailed_times_record_ratios(groups, xticklabels, result_pdf)


if __name__=="__main__":
    # Get execution time comparation plot based on a single round time records
    execution_time_folder = join("data", "results", "execution_time")
    xticklabels = [r'$\text{diff}_{\text{line}}$', r'$\text{diff}_{\text{word}}$', 'CodeMapper-5', 'CodeMapper-10', 'CodeMapper']
    result_pdf = join("data", "results", "table_plots", "execution_time_baseline_comparison_detailed_4data.pdf")
    data_type = ["annotation_a", "annotation_b", "suppression", "variable_test", "block_test", "method_test"] 
    PlotExecutionTimeComparisonDetailed(execution_time_folder, xticklabels, result_pdf, data_type).run()
