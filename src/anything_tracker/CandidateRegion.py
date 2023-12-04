class CandidateRegion():
    def __init__(self, source_region_character_range: object, 
            candidate_region_character_range: object, 
            candidate_region_character_sources: list,
            marker):
        self.source_region_character_range = source_region_character_range
        self.candidate_region_character_range = candidate_region_character_range 
        self.character_sources = candidate_region_character_sources
        self.marker = marker

def show_candidate_region(__value: object):
    print(f"Source region character range: {__value.source_region_character_range.four_element_list}.")
    print(f"Candidate region character range: {__value.candidate_region_character_range.four_element_list}.")
    print(f"Candidate characters:\n{__value.character_sources}")
    print(f"Candidate marker: {__value.marker}")
    print()

def get_candidate_region_range(__value: object):
    return __value.candidate_region_character_range.four_element_list