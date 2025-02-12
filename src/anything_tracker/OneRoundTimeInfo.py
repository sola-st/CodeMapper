class OneRoundTimeInfo():
    # TODO 
    '''
    To record execution time, has the following attributes:
        * candidate_numbers, # how many cnadidates it gets
        * compute_candidates_executing_time
        * select_target_executing_time
        * read source target files time
        * diff computation
        * number of de-duplicated diff reports
        * extract relevant hunks (also some candidates)
        * (extract candidates with overlapping hunks + text search) time
        * overalpping_round
    '''
    candidate_numbers: int
    compute_candidates_time: float
    select_target_time: float
    overall_time: float
    diff_report_num: int
    get_target_file_path_time: float
    read_source_target_file_time: float
    diff_computation: float
    extract_hunks_time: float
    get_diff_based_candis_time: float 
    get_movement_candis_time: float
    get_searched_candis_time: float
    refine_range_time: float
    extract_candidate_with_overlapping_serach_time: float
    overalpping_round: int

    def __init__(self):
        self.candidate_numbers = 1
        self.compute_candidates_time = 0
        self.select_target_time = 0
        self.overall_time = 0
        self.get_target_file_path_time = 0
        self.read_source_target_file_time = 0
        self.diff_report_num = 1
        self.diff_computation = 0
        self.extract_hunks_time = 0 # includes easy diff-based, movement, search
        # self.identify_overlapping_location_time = 0 was included in extract_hunks_time
        self.get_diff_based_candis_time = 0 # for overlapping hunk combination, in SearchLinesToCandidateRegion
        self.get_movement_candis_time = 0
        self.get_searched_candis_time = 0
        self.refine_range_time = 0 # not include the time for overlapping hunk combination 
        self.extract_candidate_with_overlapping_serach_time = 0 # overlapping hunk combination and search (includes diff-base time and search time)
        self.overalpping_round = 0

def get_time_relevant_names():
    # to be written as a hearder to the execution time file.
    names = ["candidate_numbers",
            "phase1",
            "phase2",
            "overall",
            "diff_report_num",
            "identify_target_file",
            "read_files",
            "diff_computation",
            "overlapping_location+easy_diff_candi",
            "get_diff_based_candis",
            "get_movement_candis",
            "get_searched_candis",
            "refine_range",
            "overlapping_combination+search",
            "overalpping_round"]
    return names

def update_time_records(given_object, end_time, start_time, attr_to_update):
    ori_val = getattr(given_object, attr_to_update, 0)
    new_val = f"{(float(ori_val) + (end_time - start_time) * 1000):.2f}"
    setattr(given_object, attr_to_update, new_val)
    return given_object

def get_refined_names():
    # to be used as the key for calculated rates.
    # TODO, ratio report
    names = ["identify_target_file",
            "read_files",
            "diff_computation",
            "iterate_hunks_extract_candidate",
            "overlapping_search"]
    return names