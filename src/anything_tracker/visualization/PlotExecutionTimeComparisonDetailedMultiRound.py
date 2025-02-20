# from itertools import zip_longest
from os.path import join
import numpy as np
from anything_tracker.visualization.PlotExecutionTimeComparisonDetailed \
        import PlotExecutionTimeComparisonDetailed, plot_detailed_times_record_ratios

    
class PlotExecutionTimeComparisonDetailedMultiRound(PlotExecutionTimeComparisonDetailed):
    def __init__(self, execution_time_folder, xticklabels, result_pdf, data_type):
        super().__init__(execution_time_folder, xticklabels, result_pdf, data_type)
        self.multi_round_groups = []

    def run(self):
        # colloct all execution time files acorss multiple rounds
        for round in range(1, 6): # 5 runs so far
            file_list_annodata_a = []
            file_list_annodata_b = []
            file_list_suppression = []
            for t in data_type:
                if round == 1: # the first (original) round --> the one we do the measurement
                    execution_time_file_line = join(execution_time_folder, t, f"execution_time_{t}_line.csv")
                    execution_time_file_word = join(execution_time_folder, t, f"execution_time_{t}_word.csv")
                    execution_time_file_at = join(execution_time_folder, t, f"execution_time_{t}.csv")
                else:
                    execution_time_file_line = join(execution_time_folder, f"round_{round}", t, f"execution_time_{t}_line.csv")
                    execution_time_file_word = join(execution_time_folder, f"round_{round}", t, f"execution_time_{t}_word.csv")
                    execution_time_file_at = join(execution_time_folder, f"round_{round}", t, f"execution_time_{t}.csv")
                    
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
            for k, (anno_file_a, anno_file_b, supp_file) in enumerate(zip(file_list_annodata_a, file_list_annodata_b, file_list_suppression)):
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
                print(f"*** {groups_item}")
                if (k+1) % 3 == 0:
                    print()
                self.clear_time_records()
            self.multi_round_groups.append(groups) # each element is for an entire round

        # decide the final data to show in the plot
        print()
        multi_round_detailed_avgs = []
        refined_multi_round_groups = []
        substep_num = len(groups[0]["subnumbers"])
        for approach_idx in range(len(xticklabels)):
            for idx in range(substep_num):
                multi_round_detailed_avgs.append(sum(float(group[approach_idx]["subnumbers"][idx]) for group in self.multi_round_groups) / 5)
            overall_avg = sum(multi_round_detailed_avgs) # avoid the tiny inaccuracy in the timer.
            groups_item = {'overall': overall_avg, 'subnumbers': multi_round_detailed_avgs}
            print(groups_item)
            refined_multi_round_groups.append(groups_item)
            multi_round_detailed_avgs = []

        plot_detailed_times_record_ratios(refined_multi_round_groups, xticklabels, result_pdf)


if __name__=="__main__":
    # Get execution time comparation plot based on a single round time records
    execution_time_folder = join("data", "results", "execution_time")
    xticklabels = [r'$\text{diff}_{\text{line}}$', r'$\text{diff}_{\text{word}}$', 'RegionTracker']
    result_pdf = join("data", "results", "table_plots", "execution_time_baseline_comparison_detailed_multiRound.pdf")
    data_type = ["annotation_a", "annotation_b", "suppression"] 
    PlotExecutionTimeComparisonDetailedMultiRound(execution_time_folder, xticklabels, result_pdf, data_type).run()
