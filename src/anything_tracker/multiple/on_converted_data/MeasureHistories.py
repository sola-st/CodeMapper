from collections import defaultdict
import csv
from itertools import zip_longest
import json
import os
from os.path import join
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file


def load_json_file(file):
    with open(file) as f:
        data = json.load(f)
    return data
        

class WhichMetricIsBetter():
    def __init__(self, oracle_file_folder, results_dir, results_csv_file):
        self.oracle_file_folder = oracle_file_folder
        self.results_dir = results_dir
        self.results_csv_file = results_csv_file

        self.metrics = ["Metric"]
        self.candidate_nums = ["Number of Candidates"]
        self.target_region_indices = ["Target region index"]
        self.expected = ["Expected ranges"]
        self.predicted = ["Predicted ranges"]
        self.is_matched_set = ["Exactly matched"]
        self.pre_dist = ["Pre-character distance"]
        self.post_dist = ["Post-character distance"]
        self.dists = ["Character distance"]
        self.recalls = ["Recall"]
        self.precisions = ["Precision"]
        self.f1s = ["F1-score"]
        self.notes = ["Notes"]

        # record the abs row number that should be an empty line in the output csv file.
        self.empty_line_mark = [] 

    def update_results(self, compare_results, pre, post, dist, recall, prec, f1, note="-"):
        # compare_results has 3 categories: 
        # exactly matches(Y), make sense(overalpped)(M), wrong(W). 
        self.is_matched_set.append(compare_results)
        self.pre_dist.append(pre)
        self.post_dist.append(post)
        self.dists.append(dist)
        self.recalls.append(recall)
        self.precisions.append(prec)
        self.f1s.append(f1)
        self.notes.append(note)

    def compute_to_write_measuement(self):
        # Dictionary to store grouped values
        grouped_is_matched_set = defaultdict(list)
        grouped_pre_dist = defaultdict(list)
        grouped_post_dist= defaultdict(list)
        grouped_dists = defaultdict(list)
        grouped_recalls = defaultdict(list)
        grouped_precisions = defaultdict(list)
        grouped_f1s = defaultdict(list)

        # Grouping the values
        for metric, is_matched, pre, post, dist, rec, prec, f1 in zip(self.metrics[1:], \
                    self.is_matched_set[1:], self.pre_dist[1:], self.post_dist[1:], \
                    self.dists[1:], self.recalls[1:], self.precisions[1:], self.f1s[1:]):
            grouped_is_matched_set[metric].append(is_matched)
            grouped_pre_dist[metric].append(pre)
            grouped_post_dist[metric].append(post)
            grouped_dists[metric].append(dist)
            grouped_recalls[metric].append(rec)
            grouped_precisions[metric].append(prec)
            grouped_f1s[metric].append(f1)
        
        # Calculating averages
        only_M_pre_dist_groups = {}
        only_M_post_dist_groups = {}
        only_M_dists_groups = {}
        unique_keys = set(self.metrics[1:]) # random order
        for uni_key in unique_keys:
            only_M_pre_dist_groups.update({uni_key: []})
            only_M_post_dist_groups.update({uni_key: []})
            only_M_dists_groups.update({uni_key: []})

        for metric, matches in grouped_is_matched_set.items():
            for i, match in enumerate(matches):
                if match == "M":
                    only_M_pre_dist_groups[metric].append(grouped_pre_dist[metric][i])
                    only_M_post_dist_groups[metric].append(grouped_post_dist[metric][i])
                    only_M_dists_groups[metric].append(grouped_dists[metric][i])
        averages_pre = None
        try:
            averages_pre = {k: sum(v) / len(v) for k, v in only_M_pre_dist_groups.items()}
            averages_post= {k: sum(v) / len(v) for k, v in only_M_post_dist_groups.items()}
            averages_dist = {k: sum(v) / len(v) for k, v in only_M_dists_groups.items()}
        except:
            pass

        averages_rec = {k: sum(v) / len(v) for k, v in grouped_recalls.items()}
        averages_prec = {k: sum(v) / len(v) for k, v in grouped_precisions.items()}
        averages_f1 = {k: sum(v) / len(v) for k, v in grouped_f1s.items()}

        for key in averages_rec.keys():
            self.metrics.append(key)
            match_dict = {
                "Y": grouped_is_matched_set[key].count("Y"), 
                "M": grouped_is_matched_set[key].count("M"), 
                "W": grouped_is_matched_set[key].count("W")
            }
            self.is_matched_set.append(str(match_dict))
            if averages_pre:
                self.pre_dist.append(round(averages_pre[key], 1))
                self.post_dist.append(round(averages_post[key], 1))
                self.dists.append(round(averages_dist[key], 1))
            else:
                self.pre_dist.append(0)
                self.post_dist.append(0)
                self.dists.append(round(0))
            self.recalls.append(round(averages_rec[key], 3))
            self.precisions.append(round(averages_prec[key], 3))
            self.f1s.append(round(averages_f1[key], 3))
                    
        results = zip_longest(self.metrics, self.candidate_nums, self.target_region_indices,\
                self.expected, self.predicted, self.is_matched_set, self.pre_dist, self.post_dist, self.dists, \
                self.recalls, self.precisions, self.f1s, self.notes)
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
        subfolders = os.listdir(self.oracle_file_folder)
        oracle_num = len(subfolders)
        for num in range(oracle_num):
            # expected
            oracle_expected_file = join(self.oracle_file_folder, str(num), "expect_simple.json")
            expected_commit_range_pieces:dict = load_json_file(oracle_expected_file)
            expected_commits = expected_commit_range_pieces.keys()

            url = expected_commit_range_pieces["url"]
            tmp = url.split("/")
            repo_name = tmp[-1].rstrip(".git")
            repo_dir = join("data", "repos_java", repo_name)

            # predicted
            json_results_file = join(self.results_dir, f"{num}/target.json")
            assert os.path.exists(json_results_file) == True
            histories_regions_all = load_json_file(json_results_file)

            for histories_regions in histories_regions_all:
                for region in histories_regions:
                    region_target_commit = region["target_commit"]
                    region_target_range = json.loads(region["target_range"])
                    expected_range = ""
                    if region_target_commit in expected_commits:
                        region_target_file = region["target_file"]
                        file_range_info = expected_commit_range_pieces[region_target_commit]
                        expected_range = json.loads(file_range_info["range"])
                        expected_file = file_range_info["file"]
                        if region_target_file == expected_file:
                            if region_target_range == expected_range:
                                # result 1: exact matches
                                self.update_results("Y", 0, 0, 0, 1, 1, 1)
                            else:
                                # compute distance and overlap percentage
                                target_lines = checkout_to_read_file(repo_dir, region_target_commit, region_target_file)
                                target_lines_str = "".join(target_lines)
                                target_lines_len_list = get_character_length_of_lines(target_lines)

                                if expected_range == None or region_target_range == None:
                                    self.update_results("W", -1, -1, -1, 0, 0, 0)
                                else:
                                    pre_distance, post_distance, distance, recall, precision, f1_score, compare_results = \
                                            calculate_overlap(expected_range, region_target_range, target_lines_len_list, target_lines_str)
                                    self.update_results(compare_results, pre_distance, post_distance, distance, recall, precision, f1_score)
                        else:
                            # file path is not matched
                            note = f"Commits: {region_target_commit}\nExpected: {expected_file}\nPredicted: {region_target_file}"
                            self.update_results("--", 0, 0, 0, 0, 0, 0, note)
                            print(f"File path is not matched: {region_target_commit}, {json_results_file}")
                    
                    else: # the predicted commit history is not in the expected history list.
                        self.update_results("-", 0, 0, 0, 0, 0, 0)
                        expected_range = "-" # "not in expected"
                        # print(f"Not in expected histories: {region_target_commit}, {json_results_file}")

                    self.metrics.append(region["version"])
                    self.candidate_nums.append(region["all_candidates_num"])
                    self.target_region_indices.append(region["index"])
                    self.expected.append(expected_range)
                    self.predicted.append(region_target_range)

            self.empty_line_mark.append(len(self.metrics)) # +1 is abs number, note that the csv file has title row.

        self.compute_to_write_measuement()
        

if __name__=="__main__":
    oracle_file_folder = join("data", "converted_data")
    results_dir = join("data", "results", "tracked_maps", "mapped_regions")
    results_csv_file = join("data", "results", "measurement_results", "measurement_results_metrics_attribute.csv")
    WhichMetricIsBetter(oracle_file_folder, results_dir, results_csv_file).run()