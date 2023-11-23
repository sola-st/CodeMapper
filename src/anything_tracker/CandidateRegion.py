class CandidateRegion():
    def __init__(self, candidate_region_line_numbers, candidate_region_line_sources):
        self.line_numbers = candidate_region_line_numbers
        self.line_sources = candidate_region_line_sources

def show_candidate_region(__value: object):
    print(__value.line_numbers)
    print(__value.line_sources)
    print()