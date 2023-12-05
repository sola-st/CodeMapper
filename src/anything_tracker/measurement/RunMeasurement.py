import csv
import json
import os
from os.path import join
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file

def load_json_file(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data
    
def write_results(results_list, file_name):
    with open(f"data/results/{file_name}", "w") as f:
        for sub_list in results_list:
            csv_writer = csv.writer(f)
            csv_writer.writerow(sub_list)

def main():
    candidates_dir = join("data", "results", "tracked_maps", "candidate_regions")

    # read maps file
    oracle_file = join("data", "oracle", "change_maps.json")
    maps = load_json_file(oracle_file)

    results = []
    results.append(["Ground truth index", "Number of candidates", "Exact match", "Distance", "Overlap Percentage"])

    for i, meta in enumerate(maps):
        match = []
        distance = []
        overlap = []
        target_lines = []

        url = meta["url"]
        tmp = url.split("/")
        repo_name = tmp[-3]
        target_commit = tmp[-1]
        repo_dir = join("data", "repos", repo_name)
        mapping:dict = meta["mapping"]
        file_path = mapping["target_file"]
        target_lines = checkout_to_read_file(repo_dir, target_commit, file_path)
        target_lines_str = "".join(target_lines)
        target_lines_len_list = get_character_length_of_lines(target_lines)
        
        if mapping["source_range"] == None:
            # TODO After update the ground truth, get back to remove this check.
            continue

        if mapping["target_range"] != None:
            expected_character_range = json.loads(mapping["target_range"])
        else:
            expected_character_range = [0, 0, 0, 0]

        candidate_num = 0
        json_results_file = join(candidates_dir, f"{i}/candidates.json")
        if os.path.exists(json_results_file):
            with open(json_results_file, 'r') as f:
                candidate_regions = json.load(f)

            candidate_num = len(candidate_regions)
            for candidate in candidate_regions:
                candidate_character_range = json.loads(candidate["target_range"])
                if expected_character_range == candidate_character_range:
                    match.append(candidate_character_range)
                    distance.append(0)
                    overlap.append(1.0)
                else:
                    # compute distance
                    # # TODO also separate distance
                    # compute overlap percentage
                    dist, rate = calculate_overlap(expected_character_range, candidate_character_range, target_lines_len_list, target_lines_str)
                    distance.append(dist)
                    overlap.append(rate)
                    match.append("-")
        else:
            match.append("Fail")
            distance.append("Fail")
            overlap.append("Fail")
        
        results.append([i, candidate_num, match, distance, overlap])

    write_results(results, "measurement_results.csv")

if __name__=="__main__":
    main()