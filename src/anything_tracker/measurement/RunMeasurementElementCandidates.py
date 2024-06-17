import csv
from itertools import zip_longest
import json
import os
from os.path import join
from anything_tracker.measurement.MeasureProgramElement import load_json_file
from anything_tracker.multiple.track_histories.TrackHistoryPairs import get_category_subfolder_info


class RunMeasurement():
    def __init__(self, oracle_file_folder, results_dir, results_csv_file_name):
        self.oracle_file_folder = oracle_file_folder
        self.results_dir = results_dir
        self.results_csv_file_name = results_csv_file_name
        
    def run(self):
        all = 0
        expected = ["Expected ranges"]
        predicted = ["Predicted ranges"]
        is_matched_set = ["Exactly matched"]

        # start from reading all the oracles
        subfolders = os.listdir(self.results_dir)
        ordered_subfolders = [int(num) for num in subfolders]
        ordered_subfolders.sort()
        # ordered_subfolders = list(range(20))
        for num in ordered_subfolders:
            # candidate_file = join(self.results_dir, str(num), "target.json")
            # all_targets = load_json_file(candidate_file)
            # all+= len(all_targets)
            # continue

            if not os.path.exists(join(self.results_dir, str(num))): 
                # AnythingTracker fails to get results.
                continue

            # expected
            oracle_expected_file = join(self.oracle_file_folder, str(num), "expect_simple.json")
            expected_commit_range_pieces:dict = load_json_file(oracle_expected_file)
            expected_commits = expected_commit_range_pieces.keys()

            # predicted
            json_results_candi_folder = join(self.results_dir, str(num))
            inner_folder_len = len(os.listdir(json_results_candi_folder)) -1 # note there is a target.json
            all+=inner_folder_len
            empty_candiates = False
            if inner_folder_len == 0: # only the target, null target
                empty_candiates = True
                inner_folder_len = 1
            
            for inner_num in range(inner_folder_len):
                candidate_file = join(json_results_candi_folder, f"{inner_num}/candidates.json")
                if empty_candiates == True or not os.path.exists(candidate_file):
                    candidate_file = join(json_results_candi_folder, "target.json")

                all_candidates = load_json_file(candidate_file)
                candidate_target_commit = all_candidates[0]["target_commit"] # the same for all the candiates in current candidates,json

                if candidate_target_commit in expected_commits:
                    file_range_info = expected_commit_range_pieces[candidate_target_commit]
                    expected_range = None
                    if file_range_info["range"] not in [None, "[]"]:
                        expected_range = json.loads(file_range_info["range"])

                    for candidate in all_candidates:
                        if not os.path.exists(candidate_file):
                            candidate = all_candidates[inner_num]
                        candidate_range = candidate["target_range"]
                        if candidate_range != None:
                            candidate_range = json.loads(candidate["target_range"])
                        
                        if expected_range == candidate_range:
                            is_matched_set.append("Y")
                        else:
                            is_matched_set.append("U")
                        if not os.path.exists(candidate_file):
                            break
                else:
                    is_matched_set.append("W")
                
        # add average number to each list(column in the results file) or other information as needed
        is_matched_set.append(is_matched_set.count("Y"))
                    
        results = zip_longest(expected, predicted, is_matched_set)

        write_results(results, self.results_csv_file_name)   
        print(all)

def write_results(results_set, file_name):
    with open(file_name, "w") as f:
        csv_writer = csv.writer(f)
        for row in results_set:
            csv_writer.writerow(row)


if __name__=="__main__":
    oracle_file_folder = join("data", "converted_data")
    category_subset_pairs = get_category_subfolder_info(oracle_file_folder)
    # category_subset_pairs = [["class", "training"], ["class", "test"]]
    for category, subset in category_subset_pairs:
        detailed_oracle_file_folder = join(oracle_file_folder, category, subset)
        results_dir = join("data", "results", "tracked_maps", "element", "line", f"mapped_regions_element_line_{category}_{subset}")
        results_csv_file = join("data", "results",  "measurement_results", "element", "line_candidates", f"measurement_results_candidates_{category}_{subset}.csv")
        RunMeasurement(detailed_oracle_file_folder, results_dir, results_csv_file).run()