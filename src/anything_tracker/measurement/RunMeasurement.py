import json
from os.path import join
from anything_tracker.SearchLinesToCandidateRegion import get_character_length_of_lines
from anything_tracker.measurement.CharacterDistanceAndOverlapScore import calculate_overlap
from anything_tracker.utils.ReadFile import checkout_to_read_file

def load_json_file(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data
    
def write_results(results_list, file_name):
    to_write = ""
    for m in results_list:
        to_write = f"{to_write}{m}\n"
    with open(f"data/results/{file_name}", "w") as f:
        f.write(to_write)

def main():
    candidates_dir = join("data", "results", "tracked_maps/candidate_regions")

    # read maps file
    oracle_file = join("data", "test_oracle", "change_maps_test.json")
    maps = load_json_file(oracle_file)

    exact_match_results = []
    distance_results = []
    overlap_results = []

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
        file_path = mapping["new_file"]
        target_lines = checkout_to_read_file(repo_dir, target_commit, file_path)
        target_lines_str = "".join(target_lines)
        target_lines_len_list = get_character_length_of_lines(target_lines)
        
        if mapping["old_range"] == None:
            # TODO After update the ground truth, get back to remove this check.
            continue

        if mapping["new_range"] != None:
            expected_character_range = json.loads(mapping["new_range"])
        else:
            expected_character_range = [0, 0, 0, 0]
            continue

        json_results_file = join(candidates_dir, f"results_{i}.json")
        with open(json_results_file, 'r') as f:
            candidate_regions = json.load(f)

        candidate_num = len(candidate_regions)
        if candidate_num > 20:
            continue
            
        for j, candidate in enumerate(candidate_regions):
            candidate_character_range = json.loads(candidate["new_range"])
            if expected_character_range == candidate_character_range:
                match.append(candidate_character_range)
                distance.append(0)
                overlap.append(1.0000)
            else:
                # compute distance
                # # TODO also separate distance
                # compute overlap percentage
                dis, rate = calculate_overlap(expected_character_range, candidate_character_range, target_lines_len_list, target_lines_str)
                distance.append(dis)
                overlap.append(rate)
                match.append("--")
        
        exact_match_results.append([i, candidate_num, match])
        distance_results.append([i, candidate_num, distance])
        overlap_results.append([i, candidate_num, rate])

    write_results(exact_match_results, "exact_match.txt")
    write_results(distance_results, "distance.txt")
    write_results(overlap_results, "percentage.txt")

if __name__=="__main__":
    main()