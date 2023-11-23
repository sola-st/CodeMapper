from git.repo import Repo
from anything_tracker.CandidateRegion import CandidateRegion, RegionLineIndexMap
from os.path import join


class SearchLinesToCandidateRegion():
    def __init__(self, meta):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_line_range = meta.interest_line_range
        self.interest_line_numbers = list(self.interest_line_range)

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
        self.source_region_line_numbers = []
        self.candidate_regions = []
        self.candidate_region_line_numbers = []
        self.candidate_region_line_sources = []
        self.mappings = [] 

        self.source_region_lines = self.get_source_region_lines()
        target_file_lines = self.checkout_to_read_file(self.target_commit)
        # Find the candidate_region_ranges 
        self.mappings = [[i, j] for i, a in enumerate(target_file_lines) for j, b in zip(self.interest_line_numbers, self.source_region_lines) if a != "\n" and a.strip() == b.strip()]

        if self.mappings:
            for idx_map in self.mappings:
                # idx_map format: [[1, 0], [2, 1], [5, 0], [6, 1]]
                # [1, 0] = [target_index, base_index]
                base_idx = idx_map[1]
                target_idx = idx_map[0]
                self.source_region_line_numbers.append(base_idx)
                self.candidate_region_line_numbers.append(target_idx)
                self.candidate_region_line_sources.append(target_file_lines[target_idx])
        
        # Get candidate ranges
        is_consecutive = self.check_consecutive()
        if is_consecutive == False:
            candidate_regions = self.get_sub_ranges()
        else:
            region_line_index_map = RegionLineIndexMap(self.source_region_line_numbers, self.candidate_region_line_numbers)
            candidate_regions = CandidateRegion(region_line_index_map , self.candidate_region_line_sources)

        return candidate_regions
    
    def check_consecutive(self):
        # Return True or False
        return sorted(self.candidate_region_line_numbers) == \
                list(range(min(self.candidate_region_line_numbers), max(self.candidate_region_line_numbers)+1))

    def get_sub_ranges(self):
        sub_range_base_line_numbers = []
        sub_range_target_line_numbers = []
        sub_range_line_sources = []
        region_line_index_map = []
        sub_range = []
        sub_ranges = []

        source_region_len = len(self.source_region_lines)
        candidate_regions_len = len(self.candidate_region_line_numbers)
        for i in range(candidate_regions_len):
            if self.candidate_region_line_numbers[i] != self.candidate_region_line_numbers[i-1] + 1:
                if sub_range_target_line_numbers:
                    region_line_index_map = RegionLineIndexMap(sub_range_base_line_numbers, sub_range_target_line_numbers)
                    sub_range = CandidateRegion(region_line_index_map, sub_range_line_sources) 
                    sub_ranges.append(sub_range)
                    sub_range_base_line_numbers = []
                    sub_range_target_line_numbers = []
                    sub_range_line_sources = []
                    region_line_index_map = []
                    sub_range = []

            sub_range_base_line_numbers.append(self.mappings[i][1])
            sub_range_target_line_numbers.append(self.candidate_region_line_numbers[i])
            sub_range_line_sources.append(self.candidate_region_line_sources[i])

            if sub_range_target_line_numbers and len(sub_range_target_line_numbers) % source_region_len == 0:
                region_line_index_map = RegionLineIndexMap(sub_range_base_line_numbers, sub_range_target_line_numbers)
                sub_range = CandidateRegion(region_line_index_map, sub_range_line_sources) 
                sub_ranges.append(sub_range)
                sub_range_base_line_numbers = []
                sub_range_target_line_numbers = []
                sub_range_line_sources = []
                region_line_index_map = []
                sub_range = []

        if sub_range_target_line_numbers:
            region_line_index_map = RegionLineIndexMap(sub_range_base_line_numbers, sub_range_target_line_numbers)
            sub_range = CandidateRegion(region_line_index_map, sub_range_line_sources)
            sub_ranges.append(sub_range)

        return sub_ranges