from anything_tracker.GitDiffToCandidateRegion import GitDiffToCandidateRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion

class ComputeCandidateRegions():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_line_range):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.interest_line_range = interest_line_range

    def run(self):
        candidate_regions = []
        diff_candidates = GitDiffToCandidateRegion(self).run_git_diff()
        search_candidates = SearchLinesToCandidateRegion(self).search_lines()
        candidate_regions.extend(diff_candidates)
        candidate_regions.extend(search_candidates)
        assert candidate_regions != []

        return candidate_regions