import argparse
import json
from anything_tracker.CandidateRegion import get_candidate_region_range, show_candidate_region
from anything_tracker.ComputeCandidateRegions import ComputeCandidateRegions


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--source_character_range", nargs='+', type=int, help="a 4-element list, to show where to track", required=True)
parser.add_argument("--results_json", help="the json file to put the results", required=True)


def main(repo_dir, base_commit, target_commit, file_path, source_character_range, results_dir):
    ''' 
    Step 1: Get all candidate candidates
     * 1.1 git diff changed hunks
     * 1.2 exactly mapped characters
     * 1.3 ...
    '''
    # preprocess
    interest_character_range = [idx-1 for idx in source_character_range] # all numbers starts at 0.

    # main steps
    output_maps = []

    init = ComputeCandidateRegions(repo_dir, base_commit, target_commit, file_path, interest_character_range)
    candidate_regions = init.run()

    if not candidate_regions:
        return
    # TODO change to let all numbers start at 1.
    for i, candidate in enumerate(candidate_regions):
        # print(f"Candidate #{i}:")
        # show_candidate_region(candidate)

        # TODO update to cover rename cases
        map = {
            "old_file": file_path,
            "new_file": file_path,
            "old_range": str(source_character_range),
            "new_range": str(get_candidate_region_range(candidate))
        }
        output_maps.append(map)

    # TODO Other steps

    # write results to a JSON file.
    with open(results_dir, "w", newline="\n") as ds:
        json.dump(output_maps, ds, indent=4, ensure_ascii=False)
 

if __name__ == "__main__":
    args = parser.parse_args()
    main(args.repo_dir, args.base_commit, args.target_commit, args.file_path, args.source_character_range, args.results_dir)