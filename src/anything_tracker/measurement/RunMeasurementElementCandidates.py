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
        all_candidates_num = 0
        unique_y_all = 0
        all_empty_maps = 0
        ground_truth_index = ["Ground truth indices"]
        expected = ["Expected ranges"]
        predicted = ["Predicted ranges"]
        is_matched_set = ["Exactly matched"]

        # start from reading all_candidates the oracles
        subfolders = os.listdir(self.results_dir)
        ordered_subfolders = [int(num) for num in subfolders]
        ordered_subfolders.sort()
        # ordered_subfolders = list(range(20))
        for num in ordered_subfolders:
            if not os.path.exists(join(self.results_dir, str(num))): 
                # AnythingTracker fails to get results.
                continue

            # expected
            oracle_expected_file = join(self.oracle_file_folder, str(num), "expect_simple.json")
            expected_commit_range_pieces:dict = load_json_file(oracle_expected_file)

            # predicted
            json_results_candi_folder = join(self.results_dir, str(num))
            inner_folder_len = len(os.listdir(json_results_candi_folder)) -1 # note there is a target.json
            # candidate_file = join(json_results_candi_folder, "target.json")
            # all_candidates = load_json_file(candidate_file)
            # all+=len(all_candidates)
            # continue
            
            all+=inner_folder_len
            empty_candiates = False
            if inner_folder_len == 0: # only the target, null target
                empty_candiates = True
                inner_folder_len = 1
            
            for inner_num in range(inner_folder_len):
                expected_range = None
                candidate_range = None
                expected_range_is_updated = False

                candidate_file = join(json_results_candi_folder, f"{inner_num}/candidates.json")
                if not os.path.exists(candidate_file):
                    candidate_file = join(json_results_candi_folder, "target.json")

                all_candidates = load_json_file(candidate_file)
                if candidate_file.endswith("target.json"):
                    if empty_candiates == True:
                        all_candidates_num+= len(all_candidates)
                    else:
                        all_candidates_num+=1
                else:
                    all_candidates_num+= len(all_candidates)
                    candidate_target_commit = all_candidates[0]["target_commit"] 
                    file_range_info = expected_commit_range_pieces[candidate_target_commit]

                    if file_range_info["range"] not in [None, "[]"]:
                        expected_range = json.loads(file_range_info["range"])
                    expected_range_is_updated = True

                y_exists = False
                if candidate_file.endswith("target.json"):
                    if empty_candiates == False:
                        all_candidates = [all_candidates[inner_num]]
                # if len(all_candidates) == 2:
                #     print()
                for candi_idx, candidate in enumerate(all_candidates):
                    if candidate["target_range"] not in [None, "[]", "[0, 0, 0, 0]"]:
                        candidate_range = json.loads(candidate["target_range"])

                    if expected_range_is_updated == False:
                        candidate_target_commit = candidate["target_commit"]
                        file_range_info = expected_commit_range_pieces[candidate_target_commit]
                        if file_range_info["range"] not in [None, "[]"]:
                            expected_range = json.loads(file_range_info["range"])
                    if expected_range == candidate_range:
                        is_matched_set.append("Y")
                        if y_exists == False:
                            unique_y_all+=1
                            y_exists = True
                    else:
                        is_matched_set.append("U")
                        
                    predicted.append(candidate_range)
                    expected.append(expected_range)
                    if candidate_range == expected_range == None:
                        all_empty_maps+=1
                    ground_truth_index.append(f"{num}-{inner_num}-{candi_idx}")
                    # if empty_candiates == True and candidate_file.endswith("target.json"):
                    #     break
                
        # add average number to each list(column in the results file) or other information as needed
        summary = {
            "all_histories": all,
            "all_candidates": all_candidates_num,
            "Y": is_matched_set.count("Y"),
            "unique-Y": {unique_y_all},
            "U": is_matched_set.count("U"),
        }
        is_matched_set.append(f"{summary}")
                    
        print(summary)
        print(all_empty_maps)

        results = zip_longest(ground_truth_index, expected, predicted, is_matched_set)
        write_results(results, self.results_csv_file_name)   

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