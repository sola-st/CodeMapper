from anything_tracker.CandidateRegion import show_candidate_region
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
        for candidate in candidate_regions:
            show_candidate_region(candidate)

        return candidate_regions

if __name__ == "__main__":
    # one-click test
    repo_dir = "data/repos/rails"
    base_commit = "550c5d2"
    target_commit = "2edcda8"
    file_path = "activestorage/test/jobs/transform_job_test.rb"
    interest_line_range = range(13, 14) # start at 1

    interest_line_range = range(interest_line_range.start - 1 , interest_line_range.stop - 1)
    init = ComputeCandidateRegions(repo_dir, base_commit, target_commit, file_path, interest_line_range)
    init.run()
    print("Done.")