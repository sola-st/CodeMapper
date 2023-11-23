from git.repo import Repo
from anything_tracker.CandidateRegion import CandidateRegion
from os.path import join


class SearchLinesToCandidateRegion():
    def __init__(self, meta):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_line_range = meta.interest_line_range

    def checkout_to_read_file(self, commit):
        repo = Repo(self.repo_dir)
        repo.git.checkout(commit, force=True)
        with open(join(self.repo_dir, self.file_path)) as f:
            file_lines= f.readlines()
        return file_lines

    def get_source_region_lines(self):
        base_file_lines = self.checkout_to_read_file(self.base_commit)
        start_idx = self.interest_line_range.start
        end_index = self.interest_line_range.stop
        source_region_lines = base_file_lines[start_idx:end_index]
        return source_region_lines

    def search_lines(self):
        '''
        Assuming that B is source region, and A is target file lines.
        A = [1, 2, 3, 5, 7, 2, 3]
        B = [2, 3]

        [2, 3] is a subset of [1, 2, 3, 5, 7, 2, 3] with index mapping [[1, 0], [2, 1], [5, 0], [6, 1]]
        Expected candidate ranges: [[1, 2], [5, 6]]
        '''
        source_region_lines = self.get_source_region_lines()
        target_file_lines = self.checkout_to_read_file(self.target_commit)
        # Find the candidate_region_ranges
        mappings = [[i, j] for i, a in enumerate(target_file_lines) for j, b in enumerate(source_region_lines) if a.strip() == b.strip()]

        candidate_regions = []
        candidate_region_line_numbers = []
        candidate_region_line_sources = []
        mappings_len = len(mappings)
        # Check if B is a subset of A
        is_subset = mappings_len > 0
        if is_subset == True:
            for idx_map in mappings:
                # idx_map format: [[1, 0], [2, 1], [5, 0], [6, 1]]
                target_idx = idx_map[0]
                candidate_region_line_numbers.append(target_idx)
                candidate_region_line_sources.append(target_file_lines[target_idx])
        
        # Get candidate ranges
        is_consecutive = check_consecutive(candidate_region_line_numbers)
        if is_consecutive == False:
            candidate_regions = get_sub_ranges(candidate_region_line_numbers, candidate_region_line_sources, len(source_region_lines))
        else:
            candidate_regions = CandidateRegion(candidate_region_line_numbers, candidate_region_line_sources)

        return candidate_regions
    

def check_consecutive(numbers_list):
    # Return True or False
    return sorted(numbers_list) == list(range(min(numbers_list), max(numbers_list)+1))

def get_sub_ranges(numbers_list, source_list, source_region_len):
    sub_range_line_numbers = []
    sub_range_line_sources = []
    sub_range = []
    sub_ranges = []

    for i in range(len(numbers_list)):
        if numbers_list[i] != numbers_list[i-1] + 1:
            if sub_range_line_numbers:
                sub_range = CandidateRegion(sub_range_line_numbers, sub_range_line_sources) 
                sub_ranges.append(sub_range)
                sub_range_line_numbers = []
                sub_range_line_sources = []
                sub_range = []
        sub_range_line_numbers.append(numbers_list[i])
        sub_range_line_sources.append(source_list[i])
        
        if sub_range_line_numbers and len(sub_range_line_numbers) % source_region_len == 0:
            sub_range = CandidateRegion(sub_range_line_numbers, sub_range_line_sources) 
            sub_ranges.append(sub_range)
            sub_range_line_numbers = []
            sub_range_line_sources = []
            sub_range = []

    if sub_range_line_numbers:
        sub_range = CandidateRegion(sub_range_line_numbers, sub_range_line_sources)
        sub_ranges.append(sub_range)

    return sub_ranges