class RegionLineIndexMap():
    def __init__(self, base_line_index, target_line_index): # can be 2 lists, None or ranges.
        self.base_line_index = base_line_index # indices start at 0.
        self.target_line_index = target_line_index 


class CandidateRegion():
    def __init__(self, region_line_index_map, candidate_region_line_sources):
        self.region_line_index_map = region_line_index_map # numbers start at 0.
        self.line_sources = candidate_region_line_sources

def show_candidate_region(__value: object):
    print(f"Base line index: {__value.region_line_index_map.base_line_index}.")
    print(f"Target line index: {__value.region_line_index_map.target_line_index}.")
    print(f"Candidate region: {__value.line_sources}")
    print()