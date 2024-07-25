import csv
from itertools import zip_longest
import json
import os
from os.path import join

from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file


def calculation_helper(list):
    min_value = min(list)
    max_value = max(list)
    avg_value = "{:.1f}".format((sum(list)) / len(list))
    return min_value, max_value, avg_value


class MeasureAnnotatedData():
    def __init__(self, oracle_file, results_dir, results_csv_file):
        self.oracle_file = oracle_file
        self.results_dir = results_dir
        self.results_csv_file = results_csv_file

        self.indices = ["Ground truth index"]
        self.candidate_nums = ["Number of Candidates"]
        self.target_region_indices = ["Target region index"]
        self.predicted_commits = ["Predicted commits"]
        self.change = ["Change operation"]
        self.expected = ["Expected ranges"]
        self.predicted = ["Predicted ranges"]
        self.is_matched_set = ["Range matches"]
        self.pre_dist = ["Pre-character distance"]
        self.post_dist = ["Post-character distance"]
        self.dists = ["Character distance"]
        self.recalls = ["Recall"]
        self.precisions = ["Precision"]
        self.f1s = ["F1-score"]
        self.notes = ["Notes"]

    def update_results(self, pre, post, dist, recall, precision, f1, compare_results, note=""):
        self.pre_dist.append(pre)
        self.post_dist.append(post)
        self.dists.append(dist)
        self.recalls.append(recall)
        self.precisions.append(precision)
        self.f1s.append(f1)
        self.is_matched_set.append(compare_results)
        self.notes.append(note)

    def count_exact_matches(self):
        y_num = self.is_matched_set.count("Y")
        m_num = self.is_matched_set.count("M")
        w_num = self.is_matched_set.count("W")
        match_dict = {
            "Y": y_num, 
            "M": m_num, 
            "W": w_num
        }
        # self.is_matched_set.append(f"{match_dict}")
        match_str = json.dumps(match_dict)
        self.is_matched_set.append(match_str)

    def character_distance_computation(self):
        # compute the average, min, and max of character distance, only for overlapped ranges
        overlapped_pre = [pre for pre in self.pre_dist[1:] if pre != None]
        overlapped_post = [post for post in self.post_dist[1:] if post != None]
        overlapped_dist = [dist for dist in self.dists[1:] if dist != None]

        min_pre, max_pre, avg_pre, min_post, max_post, avg_post, min_dist, max_dist, avg_dist = 0, 0 ,0, 0 ,0, 0, 0 ,0 ,0 
        if overlapped_pre:
            min_pre, max_pre, avg_pre = calculation_helper(overlapped_pre)
        if overlapped_post:
            min_post, max_post, avg_post = calculation_helper(overlapped_post)
        if overlapped_dist:
            min_dist, max_dist, avg_dist = calculation_helper(overlapped_dist)
        char_dist_dict = {
            "pre_dist": {"min": min_pre, "max": max_pre, "avg": avg_pre},
            "post_dist": {"min": min_post, "max": max_post, "avg": avg_post},
            "dist": {"min": min_dist, "max": max_dist, "avg": avg_dist}
        }
        char_dist_str = json.dumps(char_dist_dict)
        self.dists.append(char_dist_str)

    def compute_to_write_measurement(self):
        self.count_exact_matches() # 1
        self.character_distance_computation() # 2
        
        # 3
        recalls = self.recalls[1:]
        precisions = self.precisions[1:]
        f1s = self.f1s[1:]
        avg_recall = "{:.3f}".format(sum(recalls) / len(recalls))
        avg_precision = "{:.3f}".format(sum(precisions) / len(precisions))
        avg_f1 = "{:.3f}".format(sum(f1s) / len(f1s))
        self.recalls.append(avg_recall)
        self.precisions.append(avg_precision)
        self.f1s.append(avg_f1)

        # 4.1 count the file path different cases
        file_path_extras = [n for n in self.notes if "Expected:" in n]
        refer_csv_line_numbers = []
        for extra in set(file_path_extras):
            refer_csv_line_numbers.append(self.notes.index(extra))
        diff_path_str = f"path diff count: {len(file_path_extras)}\nLines: {refer_csv_line_numbers}"

        # 4.2 count the file is predicted as deleted, but expected location exists
        file_path_extras_del = [n for n in self.notes if n == "fr"]
        refer_csv_line_numbers_del = []
        for extra in set(file_path_extras_del):
            refer_csv_line_numbers_del.append(self.notes.index(extra))
        self.notes.append(f"{diff_path_str}\npath delete count: {len(file_path_extras_del)}\nLines: {refer_csv_line_numbers_del}")

        # write results
        results = zip_longest(self.indices, self.candidate_nums, self.target_region_indices, \
                self.predicted_commits, self.change, self.expected, self.predicted, self.is_matched_set, \
                self.pre_dist, self.post_dist, self.dists, self.recalls, self.precisions, self.f1s, self.notes)
        self.write_results(results)

    def write_results(self, results):
        with open(self.results_csv_file, "w") as f:
            csv_writer = csv.writer(f)
            for row in results:
                csv_writer.writerow(row)

    def run(self):
        # start from reading oracles
        with open(self.oracle_file) as f:
            maps = json.load(f)
        for i, meta in enumerate(maps):
            target_lines = []
            url = meta["url"]
            tmp = url.split("/")
            repo = tmp[-1]
            repo_dir = join("data", "repos", repo)

            # predicted
            json_results_file = join(self.results_dir, f"{i}/target.json")
            if os.path.exists(json_results_file) == True:
                self.indices.append(repo)
            else:
                continue

            # expected
            mapping:dict = meta["mapping"]
            expected_commit = mapping["target_commit"]
            expected_file = mapping["target_file"]
            
            expected_range = None
            if mapping["target_range"] != None:
                expected_range = json.loads(mapping["target_range"])

            # predicted 
            with open(json_results_file, 'r') as f:
                candidate_regions = json.load(f)

            for region in candidate_regions: 
                if region["kind"] == "no candidate regions" and "off_diff" in self.results_csv_file:
                    self.update_results(None, None, None, 0, 0, 0, "W")
                    self.candidate_nums.append(region["all_candidates_num"])
                    self.target_region_indices.append(region["index"])
                    self.predicted_commits.append(expected_commit)
                    self.change.append(region["kind"])
                    self.expected.append(expected_range)
                    self.predicted.append("no candidate regions")
                    continue
                # for target region, should be only one
                # can be multiple for candidate list

                # predicted_commit = region["target_commit"]
                # assert  predicted_commit == expected_commit # this is fixed, it starts tracking with the expected commit
                predicted_file = region["target_file"]
                predicted_range = None
                if region["target_range"] != None:
                    predicted_range = json.loads(region["target_range"])
                    if predicted_range.count(0) >= 3: # for diff deletions: [0, 0, target_hunk_range.stop, 0]
                        predicted_range = None
                    
                if predicted_file == expected_file or (predicted_file == None and expected_range == None):
                    if predicted_range == expected_range:
                        # result 1: exact matches
                        self.update_results(None, None, None, 1, 1, 1,"Y")
                    else:
                        if not expected_range or (not predicted_range):
                            self.update_results(None, None, None, 0, 0, 0, "W")
                        else:
                            target_lines = checkout_to_read_file(repo_dir, expected_commit, predicted_file)
                            target_lines_str = "".join(target_lines)
                            target_lines_len_list = get_character_length_of_lines(target_lines)
                            pre_distance, post_distance, distance, recall, precision, f1_score, compare_results =\
                                    calculate_overlap(expected_range, predicted_range, target_lines_len_list, target_lines_str)
                            self.update_results(pre_distance, post_distance, distance, recall, precision, f1_score, compare_results)
                elif predicted_file == None and expected_range != None:
                    self.update_results(None, None, None, 0, 0, 0, "file deleted but range exists", "fr") # wrong
                elif predicted_file != expected_file:
                    # file path is not matched
                    note = f"Expected: {expected_file}\nPredicted: {predicted_file}"
                    self.update_results(None, None, None, 0, 0, 0, "--", note)
                    # print(f"File path is not matched: {region_target_commit}\n{note}\n")
                
                else: # the predicted commit history is not in the expected history list.
                    self.update_results(None, None, None, None, None, None, "-")
                    expected_range = "-" # "not in expected"

                if self.indices[-1] == repo:
                    self.indices[-1] = f"{repo} - {i}"
                else: 
                    self.indices.append(i)
                self.candidate_nums.append(region["all_candidates_num"])
                self.target_region_indices.append(region["index"])
                self.predicted_commits.append(expected_commit)
                self.change.append(region["kind"])
                self.expected.append(expected_range)
                self.predicted.append(predicted_range)

        self.compute_to_write_measurement()
        
def main_ablation_study(oracle_file, results_dir_parent, results_csv_file_folder):
    ablation_settings = ["off_diff", "off_move", "off_search", "off_fine", "off_context"]
    for setting in ablation_settings:
        results_dir = join(results_dir_parent, f"mapped_regions_annodata_{setting}")
        results_csv_file = join(results_csv_file_folder, f"measurement_results_metrics_annodata_{setting}.csv")
        MeasureAnnotatedData(oracle_file, results_dir, results_csv_file).run()
        print(f"Measurement: {setting} done.")

def main_anytingtracker(oracle_file, results_dir_parent, results_csv_file_folder):
    results_dir = join(results_dir_parent, "mapped_regions_annodata")
    results_csv_file = join(results_csv_file_folder, "measurement_results_metrics_annodata.csv")
    MeasureAnnotatedData(oracle_file, results_dir, results_csv_file).run()

if __name__=="__main__":
    oracle_file = join("data", "annotation", "annotations_100.json") # to get the ground truth
    results_dir_parent = join("data", "results", "tracked_maps", "annodata") # where the target regions are
    results_csv_file_folder = join("data", "results", "measurement_results", "annodata") # to write the measurement results
    os.makedirs(results_csv_file_folder, exist_ok=True)

    # Run measurement for AnythingTracker
    main_anytingtracker(oracle_file, results_dir_parent, results_csv_file_folder)
    # Run measurement for ablation study
    main_ablation_study(oracle_file, results_dir_parent, results_csv_file_folder)