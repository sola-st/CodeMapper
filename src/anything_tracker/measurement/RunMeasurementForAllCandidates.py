import csv
from itertools import zip_longest
import json
import os
from os.path import join
from statistics import mean
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file


class RunMeasurement():
    def __init__(self, oracle_file, candidates_dir, results_csv_file_name, measurement=None):
        self.oracle_file = oracle_file
        self.candidates_dir = candidates_dir
        self.results_csv_file_name = results_csv_file_name
        self.measurement = measurement # "target.json" or "candidates.json"

    def load_json_file(self):
        with open(self.oracle_file) as f:
            data = json.load(f)
        return data
        
    def run(self):
        ground_truth_indices = ["Ground truth index"]
        candidate_nums = ["Number of Candidates"]
        target_region_indices = ["Target region index"]
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
            target_lines = []
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1]
            repo_dir = join("data", "repos", repo_name)

            mapping:dict = meta["mapping"]
            target_commit = mapping["target_commit"]
            file_path = mapping["target_file"]
            target_lines = checkout_to_read_file(repo_dir, target_commit, file_path)
            target_lines_str = "".join(target_lines)
            target_lines_len_list = get_character_length_of_lines(target_lines)
            
            if mapping["target_range"] != None:
                expected_character_range = json.loads(mapping["target_range"])
            else:
                expected_character_range = [0, 0, 0, 0]

            json_results_file = join(self.candidates_dir, f"{i}/{self.measurement}")
            assert os.path.exists(json_results_file) == True

            with open(json_results_file, 'r') as f:
                candidate_regions = json.load(f)

            c_len = len(candidate_regions)
            for j, candidate in enumerate(candidate_regions):
                candidate_character_range = candidate["target_range"]
                if candidate_character_range == None:
                    candidate_character_range = "No candidates"
                    # no candidates
                    is_matched_set.append("W")
                    pre_dist.append(-1)
                    post_dist.append(-1)
                    dists.append(-1)
                    recalls.append(0)
                    precisions.append(0)
                    f1s.append(0)
                else:
                    candidate_character_range = json.loads(candidate["target_range"])
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
                candidate_nums.append(c_len)
                target_region_indices.append(j)
                expected.append(str(expected_character_range))
                predicted.append(str(candidate_character_range))
        
        # add average number to each list(column in the results file) or other information as needed
        is_matched_set.append(is_matched_set.count("Y"))
        pre_dist.append(round(mean(pre_dist[1:]), 1))
        post_dist.append(round(mean(post_dist[1:]), 1))
        dists.append(round(mean(dists[1:]), 1))
        recalls.append(round(mean(recalls[1:]), 3))
        precisions.append(round(mean(precisions[1:]), 3))
        f1s.append(round(mean(f1s[1:]), 3))
                    
        results = zip_longest(ground_truth_indices, candidate_nums, target_region_indices, expected, predicted, is_matched_set, \
                pre_dist, post_dist, dists, recalls, precisions, f1s)

        write_results(results, self.results_csv_file_name)   

def write_results(results_set, file_name):
    with open(file_name, "w") as f:
        csv_writer = csv.writer(f)
        for row in results_set:
            csv_writer.writerow(row)


if __name__=="__main__":
    oracle_file = join("data", "annotation", "annotations_100.json")
    candidates_dir = join("data", "results", "tracked_maps", "mapped_regions")
    results_csv_file_name = join("data", "results", "measurement_results", "measurement_results_candidates.csv")
    measurement = "candidates.json"
    RunMeasurement(oracle_file, candidates_dir, results_csv_file_name, measurement).run()