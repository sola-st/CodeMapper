from collections import defaultdict
import csv
from itertools import zip_longest
import json
import os
from os.path import join


def load_json_file(file):
    with open(file) as f:
        data = json.load(f)
    return data


def compute_line_level_matches(expected_location, predicted_location):
    # compare_results has 3 categories: 
    # exactly matches(Y), make sense(overalpped)(M), wrong(W). 
    compare_results = None
    start_line1, start_char1, end_line1, end_char1 = expected_location
    start_line2, start_char2, end_line2, end_char2 = predicted_location
    expected_lines = range(start_line1, end_line1 + 1)
    predicted_lines = range(start_line2, end_line2 + 1)

    # if expected_lines == predicted_lines: # line level
    if expected_location == predicted_location: # character level
        compare_results = "Y" # "TP"
    else:
        if len(expected_lines) == 1 and expected_lines == predicted_lines: 
            # the same single line, make sure the character location also matches
            expected_characters = range(start_char1, end_char1 + 1)
            predicted_characters = range(start_char2, end_char2 + 1)
            character_intersection = list(set(expected_characters) & set(predicted_characters))
            if character_intersection:
                compare_results = "M"
            else:
                compare_results = "W" # "FP"
        else:
            intersection = list(set(expected_lines) & set(predicted_lines))
            if intersection:
                compare_results = "M" 
            else:
                compare_results = "W"

    return compare_results

class MeasureLineLevel():
    def __init__(self, oracle_file_folder, results_dir, results_csv_file):
        self.oracle_file_folder = oracle_file_folder
        self.results_dir = results_dir
        self.results_csv_file = results_csv_file

        self.indices = ["Ground truth index"]
        self.metrics = ["Metric"]
        self.candidate_nums = ["Number of Candidates"]
        self.target_region_indices = ["Target region index"]
        self.predicted_commits = ["Predicted commits"]
        self.expected = ["Expected ranges"]
        self.predicted = ["Predicted ranges"]
        self.is_matched_set = ["Line matches"]
        self.notes = ["Notes"]

        # record the abs row number that should be an empty line in the output csv file.
        self.empty_line_mark = [] 

    def update_results(self, compare_results, note=""):
        self.is_matched_set.append(compare_results)
        self.notes.append(note)

    def compute_to_write_measuement(self):
        # Dictionary to store grouped values
        grouped_is_matched_set = defaultdict(list)

        # Grouping the values
        for metric, is_matched in zip(self.metrics[1:], self.is_matched_set[1:]):
            grouped_is_matched_set[metric].append(is_matched)

        for key in grouped_is_matched_set.keys():
            self.metrics.append(key)
            y_num = grouped_is_matched_set[key].count("Y")
            m_num = grouped_is_matched_set[key].count("M")
            w_num = grouped_is_matched_set[key].count("W")
            match_dict = {
                "Y": y_num, 
                "M": m_num, 
                "W": w_num
            }
            all_cases = y_num + m_num + w_num
            recall = round((y_num / all_cases), 3)
            score_dict = {
                "recall": recall,
                "precision": recall,
                "f1-score": recall
            }
            self.is_matched_set.append(f"{match_dict}\n{score_dict}")
                    
        results = zip_longest(self.indices, self.metrics, self.candidate_nums, self.target_region_indices, \
                self.predicted_commits, self.expected, self.predicted, self.is_matched_set, self.notes)
        self.write_results(results)   

    def write_results(self, results):
        with open(self.results_csv_file, "w") as f:
            csv_writer = csv.writer(f)
            for i, row in enumerate(results):
                if i in self.empty_line_mark:
                    f.write("\n")
                csv_writer.writerow(row)

    def run(self):
        # start from reading all the oracles
        repo_folders = os.listdir(self.results_dir)
        # ordered_subfolders = list(range(20))
        for repo in repo_folders:
            # predicted
            json_results_file = join(self.results_dir, f"{repo}/target.json")
            if os.path.exists(json_results_file) == True:
                self.indices.append(repo)
            else:
                continue

            histories_regions_all = load_json_file(json_results_file)
            for region in histories_regions_all:
                ground_truth_idx = region["iteration"]
                # expected
                oracle_expected_file = join(self.oracle_file_folder, repo, ground_truth_idx, "expected_simple.json")
                expected_commit_range_pieces:dict = load_json_file(oracle_expected_file)
                expected_commits = expected_commit_range_pieces.keys()

                region_target_commit = region["target_commit"]
                region_target_range = region["target_range"]
                if region_target_range != None:
                    region_target_range = json.loads(region["target_range"])
                expected_range = None
                if region_target_commit in expected_commits:
                    region_target_file = region["target_file"]
                    file_range_info = expected_commit_range_pieces[region_target_commit]
                    if file_range_info["range"] not in [None, "[]"]:
                        expected_range = json.loads(file_range_info["range"])
                    expected_file = file_range_info["file"]
                    if region_target_file == expected_file or (region_target_file == None and expected_range == None):
                        if region_target_range == expected_range:
                            # result 1: exact matches
                            self.update_results("Y")
                        else:
                            if not expected_range or (not region_target_range):
                                self.update_results("W")
                            else:
                                compare_results = compute_line_level_matches(expected_range, region_target_range)
                                self.update_results(compare_results)
                    elif region_target_file == None and expected_range != None:
                        self.update_results("file deleted but range exists", "fr")
                    elif region_target_file != expected_file:
                        # file path is not matched
                        note = f"Expected: {expected_file}\nPredicted: {region_target_file}"
                        self.update_results("--", note)
                        print(f"File path is not matched: {region_target_commit}, {json_results_file}")
                
                else: # the predicted commit history is not in the expected history list.
                    self.update_results("-")
                    expected_range = "-" # "not in expected"

                if self.indices[-1] == repo:
                    self.indices[-1] = f"{repo} - {ground_truth_idx}"
                else: 
                    self.indices.append(ground_truth_idx)
                self.metrics.append(region["version"])
                self.candidate_nums.append(region["all_candidates_num"])
                self.target_region_indices.append(region["index"])
                self.predicted_commits.append(region_target_commit)
                self.expected.append(expected_range)
                self.predicted.append(region_target_range)

            # self.indices.pop() # pop 1 items to get enough space for the indices.
            self.empty_line_mark.append(len(self.metrics)) # +1 is abs number, note that the csv file has title row.

        self.compute_to_write_measuement()
        

if __name__=="__main__":
    oracle_file_folder = join("data", "suppression_data")
    results_dir = join("data", "results", "tracked_maps", "latest", "mapped_regions_suppression")
    results_csv_file = join("data", "results", "measurement_results", "latest", "measurement_results_metrics_suppression.csv")
    MeasureLineLevel(oracle_file_folder, results_dir, results_csv_file).run()