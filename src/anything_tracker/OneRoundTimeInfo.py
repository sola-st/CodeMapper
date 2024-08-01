class OneRoundTimeInfo():
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
    get_target_file_path_time: float
    read_source_target_file_time: float
    diff_computation: float
    diff_report_num: int
    extract_hunks_time: float
    extract_candidate_with_overlapping_serach_time: float
    overalpping_round: int

    def __init__(self):
        self.candidate_numbers = 1
        self.compute_candidates_time = 0
        self.select_target_time = 0
        self.overall_time = 0
        self.get_target_file_path_time = 0
        self.read_source_target_file_time = 0
        self.diff_computation = 0
        self.diff_report_num = 1
        self.extract_hunks_time = 0
        self.extract_candidate_with_overlapping_serach_time = 0
        self.overalpping_round = 0

def get_time_relevant_names():
    # to be written as a hearder to the execution time file.
    names = ["candidate_numbers",
            "phase1",
            "phase2",
            "overall",
            "identify_target_file",
            "read_files",
            "diff_computation",
            "diff_num",
            "iterate_hunks",
            "overlapping_search",
            "overalpping_round"]
    return names
