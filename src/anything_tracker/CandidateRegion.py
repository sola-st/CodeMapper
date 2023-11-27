class CandidateRegion():
    def __init__(self, source_region_character_range, 
            candidate_region_character_range, 
            candidate_region_character_sources):
        # ranges are object in searching, and are range or [] in git diff.
        self.source_region_character_range = source_region_character_range
        self.candidate_region_character_range = candidate_region_character_range 
        self.character_sources = candidate_region_character_sources

def show_candidate_region(__value: object):
    if isinstance(__value.source_region_character_range, list): # for git diff
        print(f"Source region character range: {__value.source_region_character_range}.")
        print(f"Candidate region character range: {__value.candidate_region_character_range}.")
    else:  # For searching lines
        print(f"Source region character range: {__value.source_region_character_range.four_element_list}.")
        print(f"Candidate region character range: {__value.candidate_region_character_range.four_element_list}.")

    print(f"Candidate region: {__value.character_sources}")
    print()

def get_candidate_region_range(__value: object):
    if isinstance(__value.source_region_character_range, list): # for git diff
        return __value.candidate_region_character_range
    else:  # For searching lines
        return __value.candidate_region_character_range.four_element_list