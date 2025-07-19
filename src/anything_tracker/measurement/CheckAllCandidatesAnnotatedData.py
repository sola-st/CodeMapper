import csv
from itertools import zip_longest
import json
import os
from os.path import join
from statistics import mean
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.measurement.CountUtils import clear_none_values, count_algorithms, count_exact_matches
from anything_tracker.utils.ReadFile import checkout_to_read_file


class RunMeasurement():
    def __init__(self, oracle_file, candidates_dir, results_csv_file_name, measurement=None, whether_check_f1s=False):
        self.oracle_file = oracle_file
        self.candidates_dir = candidates_dir
        self.results_csv_file_name = results_csv_file_name
        self.measurement = measurement # "target.json" or "candidates.json"
        self.whether_check_f1s = whether_check_f1s

    def load_json_file(self):
        with open(self.oracle_file) as f:
            data = json.load(f)
        return data
        
    def run(self):
        ground_truth_indices = ["Ground truth index"]
        candidate_nums = ["Number of Candidates"]
        target_region_indices = ["Target region index"]
        change = ["Change operation"]
        expected = ["Expected ranges"]
        predicted = ["Predicted ranges"]
        is_matched_set = ["Exactly matched"]
        pre_dist = ["Pre-character distance"]
        post_dist = ["Post-character distance"]
        dists = ["Character distance"]
        recalls = ["Recall"]
        precisions = ["Precision"]
        f1s = ["F1-score"]
        
        maps = self.load_json_file()
        for i, meta in enumerate(maps):
            mapping:dict = meta["mapping"]
            if mapping["target_range"] != None:
                expected_character_range = json.loads(mapping["target_range"])
            else:
                expected_character_range = [0, 0, 0, 0]

            target_lines_str = None
            target_lines_len_list = None

            if self.whether_check_f1s == True:
                target_lines = []
                url = meta["url"]
                tmp = url.split("/")
                repo_name = tmp[-1]
                repo_dir = join("data", "repos", repo_name)
            
                target_commit = mapping["target_commit"]
                file_path = mapping["target_file"]
                target_lines = checkout_to_read_file(repo_dir, target_commit, file_path)
                target_lines_str = "".join(target_lines)
                target_lines_len_list = get_character_length_of_lines(target_lines)
            
            json_results_file = join(self.candidates_dir, f"{i}/{self.measurement}")
            if "target" in measurement:
                assert os.path.exists(json_results_file) == True
            if not os.path.exists(json_results_file):
                json_results_file = join(self.candidates_dir, f"{i}/target.json")

            with open(json_results_file, 'r') as f:
                candidate_regions = json.load(f)

            c_len = len(candidate_regions)
            for j, candidate in enumerate(candidate_regions):
                candidate_character_range = json.loads(candidate["target_range"])
                if self.whether_check_f1s == True:
                    if candidate_character_range.count(0) > 2:
                        candidate_character_range = [0, 0, 0 ,0]

                    if expected_character_range == candidate_character_range:
                        is_matched_set.append("Y")
                        pre_dist.append(0)
                        post_dist.append(0)
                        dists.append(0)
                        recalls.append(1)
                        precisions.append(1)
                        f1s.append(1)
                    else:
                        # compute distance and overlap percentage
                        pre_distance, post_distance, distance, recall, precision, f1_score, is_meaningful = \
                                calculate_overlap(expected_character_range, candidate_character_range, target_lines_len_list, target_lines_str)
                        is_matched_set.append(is_meaningful)
                        pre_dist.append(pre_distance)
                        post_dist.append(post_distance)
                        dists.append(distance)
                        recalls.append(recall)
                        precisions.append(precision)
                        f1s.append(f1_score)

                ground_truth_indices.append(i)
                change.append(candidate["kind"])
                candidate_nums.append(c_len)
                target_region_indices.append(j)
                expected.append(str(expected_character_range))
                predicted.append(str(candidate_character_range))
        
        # add average number to each list(column in the results file) or other information as needed
        is_matched_set = count_exact_matches(is_matched_set)
        if whether_check_f1s == True:
            cleared_pre_dist = clear_none_values(pre_dist)
            pre_dist.append(round(mean(cleared_pre_dist[1:]), 1))
            cleared_post_dist = clear_none_values(post_dist)
            post_dist.append(round(mean(cleared_post_dist[1:]), 1))
            cleared_dists = clear_none_values(dists)
            dists.append(round(mean(cleared_dists[1:]), 1))
            recalls.append(round(mean(recalls[1:]), 3))
            precisions.append(round(mean(precisions[1:]), 3))
            f1s.append(round(mean(f1s[1:]), 3))
        count_algorithms(change)
                    
        results = zip_longest(ground_truth_indices, candidate_nums, target_region_indices, change, expected, predicted, is_matched_set, \
                pre_dist, post_dist, dists, recalls, precisions, f1s)

        write_results(results, self.results_csv_file_name)   


def write_results(results_set, file_name):
    with open(file_name, "w") as f:
        csv_writer = csv.writer(f)
        for row in results_set:
            csv_writer.writerow(row)


if __name__=="__main__":
    dataset = "annotation_b" # cna be "annotation_a", "annotation_b", "suppression", "variable", "block", "method"
    oracle_file = join("data", "annotation", f"{dataset}.json")
    candidates_dir = join("data", "results", "tracked_maps", dataset, f"mapped_regions_{dataset}")
    results_csv_file_name = join("data", "results", "measurement_results", dataset, f"measurement_results_candidates_{dataset}.csv")
    measurement = "candidates.json"
    whether_check_f1s = False
    RunMeasurement(oracle_file, candidates_dir, results_csv_file_name, measurement, whether_check_f1s).run()