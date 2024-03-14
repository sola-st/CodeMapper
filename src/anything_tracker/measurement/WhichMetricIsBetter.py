from collections import defaultdict
import csv
from itertools import zip_longest
import json
import os
from os.path import join
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file


class WhichMetricIsBetter():
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
        metrics = ["Metric"]
        ground_truth_indices = ["Ground truth index"]
        candidate_nums = ["Number of Candidates"]
        target_region_indices = ["Target region index"]
        change_operations = ["Change Type"]
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

            for candidate in candidate_regions:
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

                metrics.append(candidate["version"])
                ground_truth_indices.append(i)
                candidate_nums.append(candidate["all_candidates_num"])
                change_operations.append(mapping["change_operation"])
                target_region_indices.append(candidate["index"])
                expected.append(expected_character_range)
                predicted.append(candidate_character_range)
        
        # Dictionary to store grouped values
        grouped_is_matched_set = defaultdict(list)
        grouped_pre_dist = defaultdict(list)
        grouped_post_dist= defaultdict(list)
        grouped_dists = defaultdict(list)
        grouped_recalls = defaultdict(list)
        grouped_precisions = defaultdict(list)
        grouped_f1s = defaultdict(list)

        # Grouping the values
        for metric, is_matched, pre, post, dist, rec, prec, f1 in zip(metrics[1:], is_matched_set[1:], \
                    pre_dist[1:], post_dist[1:], dists[1:], recalls[1:], precisions[1:], f1s[1:]):
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
        unique_keys = set(metrics[1:]) # random order
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

        averages_pre = {k: sum(v) / len(v) for k, v in only_M_pre_dist_groups.items()}
        averages_post= {k: sum(v) / len(v) for k, v in only_M_post_dist_groups.items()}
        averages_dist = {k: sum(v) / len(v) for k, v in only_M_dists_groups.items()}

        averages_rec = {k: sum(v) / len(v) for k, v in grouped_recalls.items()}
        averages_prec = {k: sum(v) / len(v) for k, v in grouped_precisions.items()}
        averages_f1 = {k: sum(v) / len(v) for k, v in grouped_f1s.items()}

        for key in averages_pre.keys():
            metrics.append(key)
            match_dict = {
                "Y": grouped_is_matched_set[key].count("Y"), 
                "M": grouped_is_matched_set[key].count("M"), 
                "W": grouped_is_matched_set[key].count("W")
            }
            is_matched_set.append(str(match_dict))
            pre_dist.append(round(averages_pre[key], 1))
            post_dist.append(round(averages_post[key], 1))
            dists.append(round(averages_dist[key], 1))
            recalls.append(round(averages_rec[key], 3))
            precisions.append(round(averages_prec[key], 3))
            f1s.append(round(averages_f1[key], 3))
                    
        results = zip_longest(metrics, ground_truth_indices, candidate_nums, target_region_indices, change_operations, 
                expected, predicted, is_matched_set, pre_dist, post_dist, dists, recalls, precisions, f1s)
        write_results(results, self.results_csv_file_name)   

def write_results(results, file_name):
    with open(f"data/results/{file_name}", "w") as f:
        csv_writer = csv.writer(f)
        for i, row in enumerate(results):
            if i > 3 and "dist_based" in row:
                f.write("\n")
            csv_writer.writerow(row)


if __name__=="__main__":
    oracle_file = join("data", "annotation", "annotations_100.json")
    candidates_dir = join("data", "results", "tracked_maps", "mapped_regions")
    results_csv_file_name = join("measurement_results", "measurement_results_metrics.csv")
    measurement = "target.json" 
    WhichMetricIsBetter(oracle_file, candidates_dir, results_csv_file_name, measurement).run()