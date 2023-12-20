import os
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion, get_character_length_of_lines
from anything_tracker.utils.TransferRanges import transfer_2_indices_to_4
from anything_tracker.web_connect_specific.GitDiffToCandidateRegionUI import GitDiffToCandidateRegionUI


class AnythingTracker():
    def __init__(self, source_file_lines:str, target_file_lines:str, 
                source_start, source_end, source_region_characters:str, results_dir):
        self.source_file_lines = source_file_lines
        self.target_file_lines = target_file_lines

        # change the character string to list
        tmp = source_region_characters.split("\n")
        self.source_region_characters = [f"{t}\n" for t in tmp[:len(tmp)-1]]
        if tmp[-1] != "":
            self.source_region_characters.append(tmp[-1])

        source_lines_len_list = get_character_length_of_lines(source_file_lines)
        interest_character_range = transfer_2_indices_to_4(source_start, source_end, source_lines_len_list)
        self.interest_character_range = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
            
        self.results_dir = results_dir

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
        return target_candidate