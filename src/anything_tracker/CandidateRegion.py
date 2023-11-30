class CandidateRegion():
    def __init__(self, source_region_character_range: object, 
            candidate_region_character_range: object, 
            candidate_region_character_sources: list):
        self.source_region_character_range = source_region_character_range
        self.candidate_region_character_range = candidate_region_character_range 
        self.character_sources = candidate_region_character_sources

def show_candidate_region(__value: object):
    print(f"Source region character range: {__value.source_region_character_range.four_element_list}.")
    print(f"Candidate region character range: {__value.candidate_region_character_range.four_element_list}.")
    print(f"Candidate region: {__value.character_sources}")
    print()

def get_candidate_region_range(__value: object):
    # TODO unify numbers starts at 1.
    start_at_zero_numbers = [num+1 for num in __value.candidate_region_character_range.four_element_list]
    return start_at_zero_numbers