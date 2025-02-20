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
    colors = ["#780C28", "#B3D8A8", "#F08080", "#FAC45A", "#7A70B5", "#C8AAAA"]
    segment_labels = ['Identify target file', 'diff computation', 'Diff-Based Candidate Extraction',
                      'Movement Detection', 'Text Search', 'Target Region Selection']

    # Create the figure and axes
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams.update({'font.size': 10})
    fig, ax = plt.subplots(figsize=(4.5, 3))

    # Position of the bars on the x-axis
    bar_width = 0.4
    group_positions = range(len(groups))
    
    # Loop over each group to plot
    for i, (group, approach) in enumerate(zip(groups, xticklabels)):
        ratios = {"Approach": approach}
        overall = group['overall']
        subnumbers = group['subnumbers']
        ratios.update({"Overall": f"{(overall):.4f}"})
        ratios.update({"Phase_1": f"{(overall - subnumbers[-1]):.4f}"})
        bottom = 0  # Start position for the first segment in this group
        for subnumber, color, substep in zip(subnumbers, colors, segment_labels):
            ax.bar(i, subnumber, width=bar_width, bottom=bottom, color=color)
            bottom += subnumber
            # Compute ratio
            ratio = f"{(subnumber / overall * 100):.2f}%"  
            ratios.update({substep: f"{subnumber:.4f} ({ratio})"})
        all_ratios.append(ratios)

    # Customize the plot
    ax.set_xticks(group_positions)
    ax.set_xticklabels(xticklabels)
    
    max_overall = max(group['overall'] for group in groups)

    # Determine the number of float places in the max_overall to round to
    precision = -int(math.floor(math.log10(max_overall))) + 1
    increment = 10**-precision

    # Determine the new y-axis upper limit by rounding up
    new_ylim = math.ceil(max_overall / increment) * increment + 3 * increment
    ax.set_ylim(0, new_ylim)

    plt.ylabel('Execution time (milliseconds)')
    ax.legend(loc="upper left", prop={'size': 10}, \
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
        file_list_annodata_a = []
        file_list_annodata_b = []
        file_list_suppression = []

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
        for anno_file_a, anno_file_b, supp_file in zip_longest(file_list_annodata_a, file_list_annodata_b, file_list_suppression):
            self.get_detailed_execution_time(anno_file_a)
            self.get_detailed_execution_time(anno_file_b)
            self.get_detailed_execution_time(supp_file)

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
    xticklabels = [r'$\text{diff}_{\text{line}}$', r'$\text{diff}_{\text{word}}$', 'RegionTracker']
    result_pdf = join("data", "results", "table_plots", "execution_time_baseline_comparison_detailed.pdf")
    data_type = ["annotation_a", "annotation_b", "suppression"] 
    PlotExecutionTimeComparisonDetailed(execution_time_folder, xticklabels, result_pdf, data_type).run()
