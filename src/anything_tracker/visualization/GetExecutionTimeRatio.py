import csv
import json
import numpy as np
from os.path import join

from anything_tracker.OneRoundTimeInfo import get_refined_names

    
def get_detailed_execution_time(time_file):
    overall_time = []
    identify_target_file_time = []
    read_file_time = []
    diff_computation_time = []
    iterate_hunk_time = []
    overlapping_search_time = []

    with open(time_file, "r") as f:
        csv_reader = csv.reader(f)
        line_list = list(csv_reader)[1:]
        for line in line_list:
            if line:
                overall_time.append(float(line[4]))
                identify_target_file_time.append(float(line[5]))
                read_file_time.append(float(line[6]))
                diff_computation_time.append(float(line[7]))
                iterate_hunk_time.append(float(line[9]))
                overlapping_search_time.append(float(line[10]))

        return overall_time, identify_target_file_time, read_file_time, \
                diff_computation_time, iterate_hunk_time, overlapping_search_time


if __name__=="__main__":
    rate_record_file = join("data", "results", "table_plots", "execution_time_rates.json")
    execution_time_folder = join("data", "results", "execution_time")
    data_type = ["annodata", "suppression"]
    approaches = ["line", "word", "AnythingTracker"]

    all_rates = []
    for i, approach in enumerate(approaches):
        file_annodata = None
        file_suppression = None

        for j, t in enumerate(data_type):
            if i < 2:
                execution_time_file_at = join(execution_time_folder, t, f"execution_time_{t}_{approach}.csv")
            else:
                execution_time_file_at = join(execution_time_folder, t, f"execution_time_{t}.csv")

            if j == 0:
                file_annodata = execution_time_file_at
            else:
                file_suppression = execution_time_file_at

        
        overall_time, identify_target_file_time, read_file_time, diff_computation_time, \
                iterate_hunk_time, overlapping_search_time = get_detailed_execution_time(file_annodata)
        overall_time_suppression, identify_target_file_time_suppression, read_file_time_suppression, diff_computation_time_suppression, \
                iterate_hunk_time_suppression, overlapping_search_time_suppression = get_detailed_execution_time(file_suppression)
            
        overall_time.extend(overall_time_suppression)
        identify_target_file_time.extend(identify_target_file_time_suppression)
        read_file_time.extend(read_file_time_suppression)
        diff_computation_time.extend(diff_computation_time_suppression)
        iterate_hunk_time.extend(iterate_hunk_time_suppression)
        overlapping_search_time.extend(overlapping_search_time_suppression)

        # compute the avg numbers
        overall_avg = np.mean(overall_time)
        detailed_avgs = [np.mean(identify_target_file_time), np.mean(read_file_time), \
                np.mean(diff_computation_time), np.mean(iterate_hunk_time), np.mean(overlapping_search_time)]
        
        names = get_refined_names()
        ratios = {"approach": approach}
        for key, avg in zip(names, detailed_avgs):
            rate = f"{(avg/overall_avg):.4f}"
            ratios.update({key: f"{avg} ({rate})"})

        all_rates.append(ratios)

    with open(rate_record_file, "w") as ds:
        json.dump(all_rates, ds, indent=4, ensure_ascii=False)
    
