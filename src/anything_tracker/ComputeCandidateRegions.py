from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.GitDiffToCandidateRegion import GitDiffToCandidateRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion

class ComputeCandidateRegions():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_character_range):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.interest_character_range = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)

    def run(self):
        candidate_regions = []
        diff_candidates, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks, is_large_diff = GitDiffToCandidateRegion(self).run_git_diff()
        search_candidates = SearchLinesToCandidateRegion(self, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).search_maps()
        candidate_regions.extend(diff_candidates)
        candidate_regions.extend(search_candidates)
        if candidate_regions == []:
            if is_large_diff == True:
                print(f"--Large diff.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")
            else:
                print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")

        return candidate_regions