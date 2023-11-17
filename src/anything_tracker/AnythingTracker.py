import argparse
from anything_tracker.ComputeCandidateHunks import ComputeCandidateHunks
from anything_tracker.ComputeSimilarityScores import ComputeSimilarityScores
from anything_tracker.GetDiffResults import GetDiffResults
from anything_tracker.LineMap import show_line_map
from anything_tracker.Hunk import show_hunk


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--interest_element_character_range", help="a 4-element list, to show where to track", required=True)


def character_range_to_line_range(interest_element_character_range):
    '''   
    interest_element_character_range: 
        start_line, 
        start_character_index, 
        end_line, 
        end_character_index
    all start at 1.
    '''
    interest_line_range = ""
    interest_start_line = interest_element_character_range[0]
    interest_end_line = interest_element_character_range[2]
    interest_line_range = range(interest_start_line, interest_end_line+1)
    return interest_line_range

def main(repo_dir, base_commit, target_commit, file_path, interest_line_range):
    all_line_maps = []
    all_fine_grained_base_hunks = []
    all_intra_file_candidate_hunks = []

    # Step 1: Run git diff to get changed hunks
    diff_init = GetDiffResults(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    intra_file_hunk_pairs = diff_init.run_git_diff()

    # Step 2: Get fine grained hunks and candidate hunks
    for hunk_info in intra_file_hunk_pairs:
        candidate_init = ComputeCandidateHunks(interest_line_range, hunk_info)
        fine_grained_base_hunks, intra_file_candidate_hunks, single_line_maps = candidate_init.get_fine_grained_base_hunk_and_candidate_hunks()
        all_intra_file_candidate_hunks.extend(intra_file_candidate_hunks)
        if fine_grained_base_hunks:
            all_fine_grained_base_hunks.extend(fine_grained_base_hunks)
        if single_line_maps:  # All are no changed lines, and been mapped
            all_line_maps = single_line_maps
            break

    # Step 3: Calculate similarities for the candidate hunks
    # all indicates all the hunks related to current interest element
    similarity_init = ComputeSimilarityScores(all_fine_grained_base_hunks, all_intra_file_candidate_hunks)
    hungarian_hunk_maps = similarity_init.hungarian_assignment_hunk_level()
    hungarian_line_maps = similarity_init.hungarian_assignment_line_level()
    all_line_maps.extend(hungarian_line_maps)

    print("** maps")
    for map in all_line_maps:
        show_line_map(map)

    print("** base")
    for hunk in all_fine_grained_base_hunks:
        show_hunk(hunk)

    print("** candidate")
    for hunk in all_intra_file_candidate_hunks:
        show_hunk(hunk)
    # TODO process all_line_maps to get character level mappings


if __name__ == "__main__":
    # args = parser.parse_args()
    # interest_line_range = character_range_to_line_range(args.interest_element_character_range)
    # main(args.repo_dir, args.base_commit, args.target_commit, args.file_path, interest_line_range)

    # one-click test
    repo_dir = "data/repos/suppression-test-python-side-branches"
    # "3c571df" is the first parent of "dc1df75", 2 adjacent commits on the same branch
    base_commit = "3c571df"
    target_commit = "dc1df75"
    file_path = "greeting.py"
    interest_element_character_range = [13, 0, 13, 20]
    # interest_line_range = range(12, 13)
    interest_line_range = character_range_to_line_range(interest_element_character_range)
    main(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    print("Done.")