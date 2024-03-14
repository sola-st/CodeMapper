from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange


class BaseGitToCandidateRegion():
    def __init__(self, meta, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks):
        self.interest_character_range = meta.interest_character_range # class instance
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.source_region_characters = meta.source_region_characters
        self.target_file_lines = meta.target_file_lines

        self.top_diff_hunk = None
        if top_diff_hunks:
            self.top_diff_hunk = top_diff_hunks[0] # DiffHunk 

        self.middle_diff_hunks = middle_diff_hunks # DiffHunk 

        self.bottom_diff_hunk = None
        if bottom_diff_hunks:
            self.bottom_diff_hunk = bottom_diff_hunks[0] # DiffHunk 

        self.source_character_lens = []
        

    def get_diff_maps(self):
        '''
        Get candidates by searching the exactly mapping characters in target file.
        Get candidates based on git diff identified overlapped changed hunks.
        Return a list of character ranges: candidate_regions.

        [Top]
        Scenario 1: 
            top diff hunk + [optional] middle diff hunk(s) + no changed lines 
            --> candidate: top diff hunk + no changed lines (cover all line in between)
        Scenario 2: 
            top diff hunk + ... + bottom_diff_hunk
            --> candidate: top diff hunk + bottom_diff_hunk (cover all lines in between)
        [Middle]
        Scenario 3: 
            no changed lines + middle diff hunk(s) + no changed lines 
            --> candidate: no changed lines + no changed lines (cover all line in between)
        [Bottom]
        Scenario 4: 
            no changed lines + [optional] middle diff hunk(s) + no changed lines + bottom diff hunk
            --> candidate: top diff hunk + no changed lines (cover all line in between)
         * Also Scenario 2.
        '''

        candidate_regions = []

        if self.top_diff_hunk:
            candidate_regions = self.combine_diff_and_unchanged_ranges("top")
        elif self.bottom_diff_hunk: # Scenario 4
            candidate_regions = self.combine_diff_and_unchanged_ranges("bottom")
        elif self.middle_diff_hunks: # Scenario 3
            first_unchanged_line_numbers, last_unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(self.middle_diff_hunks)
            start_line = self.middle_diff_hunks[0].target_start_line_number - len(first_unchanged_line_numbers)
            end_line = self.middle_diff_hunks[-1].target_end_line_number -1 + len(last_unchanged_line_numbers)
            candidate_characters = self.target_file_lines[end_line-1]
            end_char = len(candidate_characters)
            region_range = [start_line, 1, end_line, end_char]
            candidate_region_range = CharacterRange(region_range)
            marker = "<COVER_IN_BETWEEN>"
            candidate_regions = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)

        if candidate_regions == []:
            return candidate_regions # return empty list
        return [candidate_regions] # return non-empty 1-dimension list
    
    def combine_diff_and_unchanged_ranges(self, location):
        '''
        Here the interest_character_range has the following structure:
        Diff hunk at top:
         * changed lines
         * unchanged lines

        or diff hunk at bottom
         * unchanged lines
         * changed lines

        Search to map the unchanged lines, and concatenate the results to changed diff hunk.
        '''

        specified_diff_hunks = []
        bottom_unchanged_line_numbers = []

        if location == "top":
            # Identify the unchanged line numbers
            if not self.bottom_diff_hunk:
                # Scenario 1
                specified_diff_hunks.append(self.top_diff_hunk)
                if self.middle_diff_hunks:
                    # also remove the changed lines in middle hunk when identify the unchanged lines
                    specified_diff_hunks.extend(self.middle_diff_hunks)
                bottom_unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, False, True)
                end_line = specified_diff_hunks[-1].target_end_line_number - 1 + len(bottom_unchanged_line_numbers)
                candidate_characters = self.target_file_lines[end_line-1]
                end_char = len(candidate_characters)
                region_range = [self.top_diff_hunk.base_start_line_number, 1, end_line, end_char]
                candidate_region_range = CharacterRange(region_range)
                marker = "<TOP_OVERLAP>"
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
                return candidate_region
            else:
                # Scenario 2: top diff hunk + ... + bottom diff hunk
                end_line = self.bottom_diff_hunk.target_end_line_number - 1
                candidate_characters = self.target_file_lines[end_line-1]
                end_char = len(candidate_characters)
                region_range = [self.top_diff_hunk.base_start_line_number, 1, end_line, end_char]
                candidate_region_range = CharacterRange(region_range)
                marker = "<TOP_BOTTOM_OVERLAP>"
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
                return candidate_region
        else: # "bottom"
            # Scenario 4
            if self.middle_diff_hunks:
                specified_diff_hunks.extend(self.middle_diff_hunks)
            specified_diff_hunks.append(self.bottom_diff_hunk)
            unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, True, False)
            start_line = specified_diff_hunks[0].target_start_line_number - len(unchanged_line_numbers)
            end_line = self.bottom_diff_hunk.target_end_line_number - 1
            candidate_characters = self.target_file_lines[end_line-1]
            end_char = len(candidate_characters)
            region_range = [start_line, 1, end_line, end_char]
            candidate_region_range = CharacterRange(region_range)
            marker = "<BOTTOM_OVERLAP>"
            candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
            return candidate_region

    def get_first_and_last_unchanged_line_numbers(self, specified_diff_hunks, first=True, last=True):
        '''
        [Top] return the first unchanged line and the size of unchanged lines after the last changed hunks
            expected start line number = the very first top hunk.start
            expected end line number = top(+middle) hunk.end + unchanged lines

        [Bottom] return the first unchanged line before the first changed hunk
            expected start line number = the first unchanged line
            expected end line number = the last bottom hunk.end-1

        [Middle] return the first unchanged line number for the upper part, and the last unchanged line for the lower part
        '''
        # get all the no changed line numbers
        changed_line_numbers = []
        for hunk in specified_diff_hunks:
            hunk_range = range(hunk.base_start_line_number, hunk.base_end_line_number)
            changed_line_numbers.extend(list(hunk_range))
        unchanged_line_numbers = list(set(self.interest_line_numbers) - set(changed_line_numbers))
        unchanged_line_numbers.sort()
        for hunk in specified_diff_hunks:
            if hunk.base_start_line_number == hunk.base_end_line_number:
                break_point = unchanged_line_numbers.index(hunk.base_start_line_number) + 1
                unchanged_line_numbers.insert(break_point, -2)
        unchanged_num = len(unchanged_line_numbers)

        # Forward iteration, get first_unchanged_line_numbers
        if first == True:
            first_unchanged_line_numbers = [] 
            for i in range(unchanged_num):
                if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] + 1:
                    if first_unchanged_line_numbers:
                        break
                    else:
                        first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 
                else:
                    first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 
            assert first_unchanged_line_numbers != []

        # Backward iteration, get last_unchanged_line_numbers
        if last == True:
            last_unchanged_line_numbers = []
            unchanged_line_numbers.reverse()
            for i in range(unchanged_num):
                if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] - 1:
                    if last_unchanged_line_numbers:
                        break
                    else:
                        last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i]) 
                else:
                    last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i])
            assert last_unchanged_line_numbers != []
        
        if first == True and last == True:
            return first_unchanged_line_numbers, last_unchanged_line_numbers
        elif first == True and last == False:
            return first_unchanged_line_numbers
        elif first == False and last == True:
            return last_unchanged_line_numbers