class SpecifyToTurnOffTechniques():
    '''
    3 techniques can be optionally turned off, support turn off one or multiple at a time.
    1. move detection
    2. search matches
    3. fine-grain borders
    '''
    def __init__(self, turn_off_techniques:list):
        # change the boolean to True to turn off the corresponding technique.
        # turn_off_techniques = [False, False, False] 
        self.trun_off_diff_candidate_extraction = turn_off_techniques[0]
        self.turn_off_move_detection = turn_off_techniques[1]
        self.turn_off_search_matches = turn_off_techniques[2]
        self.turn_off_fine_grains = turn_off_techniques[3]

    def get_all(self):
        return self.trun_off_diff_candidate_extraction, self.turn_off_move_detection, \
                self.turn_off_search_matches, self.turn_off_fine_grains