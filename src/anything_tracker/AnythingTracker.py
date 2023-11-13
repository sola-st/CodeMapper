import argparse
from anything_tracker.GetSingleLineMaps import GetSingleLineMaps

from anything_tracker.GitDiffToTargetChangedHunk import GitDiffToTargetChangedHunk
from anything_tracker.LineMap import show_maps


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
    # run git diff to get changed hunks
    init = GitDiffToTargetChangedHunk(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    hunk_info = init.run_git_diff()
    # from changed hunk to line maps
    second = GetSingleLineMaps(interest_line_range, hunk_info)
    single_line_maps = second.further_process_target_change_hunk()
    for map in single_line_maps:
        show_maps(map)
    # TODO how to organize the maps


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
    interest_element_character_range = [12, 0, 12, 20]
    # interest_line_range = range(12, 13)
    interest_line_range = character_range_to_line_range(interest_element_character_range)
    main(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    print("Done.")