import argparse
import os
from anything_tracker.CandidateRegion import show_candidate_region
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion, get_character_length_of_lines
from anything_tracker.utils.TransferRanges import transfer_2_indices_to_4
from anything_tracker.web_connect_specific.GitDiffToCandidateRegionUI import GitDiffToCandidateRegionUI


# parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
# parser.add_argument("--source_file_path", help="the source file that you want to track", required=True)
# parser.add_argument("--target_file_path", help="the target file that you want to track", required=True)
# parser.add_argument("--source_version", help="the 1st version of the target file", required=True)
# parser.add_argument("--target_version", help="the 2nd version of the target file", required=True)
# parser.add_argument("--source_start", help="the start character index of source region", required=True)
# parser.add_argument("--source_end", help="the end character index of source region", required=True)
# parser.add_argument("--source_region_characters", help="the characters of source region", required=True)
# parser.add_argument("--results_dir", help="Directory to put the results", required=True)


class AnythingTracker():
    def __init__(self, source_file_lines:str, target_file_lines:str, 
                source_start, source_end, source_region_characters, results_dir):
        self.source_file_lines = source_file_lines
        self.target_file_lines = target_file_lines
        self.source_region_characters = source_region_characters
        self.results_dir = results_dir

        source_lines_len_list = get_character_length_of_lines(source_file_lines)
        interest_character_range = transfer_2_indices_to_4(source_start, source_end, source_lines_len_list)
        self.interest_character_range = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
            
        self.source_region_characters = []

    def run(self):
        # create output folder
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        candidate_regions = []
        
        # get candidates from git diff
        diff_candidates, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = GitDiffToCandidateRegionUI(self).run_git_diff()
        # search to map characters
        search_candidates = SearchLinesToCandidateRegion(self, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).search_maps()
        candidate_regions.extend(diff_candidates)
        candidate_regions.extend(search_candidates)
        if candidate_regions == []:
            return None
        
        # get the top-1 candidate as target region.
        source_region_characters_str = "".join(self.source_region_characters)
        target_candidate, target_candidate_edit_distance, target_candidate_bleu_score = ComputeTargetRegion(
                source_region_characters_str, candidate_regions).run()
        show_candidate_region(target_candidate)
        # return target_candidate
        
if __name__ == "__main__":
    source_file_lines = ["This is a test.\n", "Hello, tester.\n", "Have a nice day!\n"]
    target_file_lines = ["This is a test.\n", "Hello, tester A.\n", "Have a nice day!\n"]
    source_start = 1
    source_end = 42
    source_region_characters = "This is a test.\n", "Hello, tester.\n", "Ha"
    results_dir = "tests/a19_stash"
    AnythingTracker(source_file_lines, target_file_lines, source_start, source_end, source_region_characters, results_dir).run()