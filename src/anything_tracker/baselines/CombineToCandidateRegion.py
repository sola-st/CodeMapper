from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import get_region_characters


class CombineToCandidateRegion():
    def __init__(self, algorithm, meta, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks):
        self.algorithm = algorithm
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
        

    def search_maps(self):
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
        self.target_lines_len_list = get_character_length_of_lines(self.target_file_lines)

        if self.top_diff_hunk:
            candidate_regions = self.combine_diff_and_search_ranges("top")
        elif self.bottom_diff_hunk: 
            candidate_regions = self.combine_diff_and_search_ranges("bottom")
        elif self.middle_diff_hunks: 
            candidate_regions = self.cover_changed_lines_in_between()

        return candidate_regions
    
    def combine_diff_and_search_ranges(self, location):
        '''
        Here the interest_character_range has the following structure:
        Diff hunk at top:
         * changed lines
         * unchanged lines

        or diff hunk at bottom
         * unchanged lines
         * changed lines

        Get the unchanged lines, and concatenate the results to changed diff hunk.
        '''

        specified_diff_hunks = []

        if location == "top":
            # Identify the unchanged line numbers
            if not self.bottom_diff_hunk:
                # Scenario 1
                specified_diff_hunks.append(self.top_diff_hunk)
                if self.middle_diff_hunks:
                    # also remove the changed lines in middle hunk when identify the unchanged lines
                    specified_diff_hunks.extend(self.middle_diff_hunks)
                unchanged_line_number = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, False, True)
                candidate_region_top_with_changed_lines = self.top_overlap(unchanged_line_number)
                return candidate_region_top_with_changed_lines
            else:
                # Scenario 2: top diff hunk + ... + bottom diff hunk
                candidate_region_top_bottom_with_changed_lines = self.top_bottom_overlap()
                return candidate_region_top_bottom_with_changed_lines
        else: # "bottom"
            # Scenario 4
            if self.middle_diff_hunks:
                specified_diff_hunks.extend(self.middle_diff_hunks)
            specified_diff_hunks.append(self.bottom_diff_hunk)
            unchanged_line_number = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, True, False)
            candidate_region_bottom_with_changed_lines = self.bottom_overlap(unchanged_line_number)
            return candidate_region_bottom_with_changed_lines
            
    def top_bottom_overlap(self):
        candidate_region_top_bottom_with_changed_lines = []

        # 5 base values
        range_start_line = self.top_diff_hunk.target_start_line_number
        range_start_char = self.top_diff_hunk.target_start_character
        range_end_line = self.bottom_diff_hunk.target_end_line_number - 1
        range_end_char = self.bottom_diff_hunk.target_end_character
        marker = f"<{self.algorithm}><TOP_BOTTOM_OVERLAP>"

        # update the 5 values
        # check if top hunk is a delete hunk
        if self.top_diff_hunk.target_start_line_number == self.top_diff_hunk.target_end_line_number:      
            # = bottom overlap 
            range_start_line = self.top_diff_hunk.target_start_line_number+1
            range_start_char = self.interest_character_range.characters_start_idx
            marker += "<TOP_DELETE>"

        # check if bottom hunk is a delete hunk, from non-empty lines to None.
        if self.bottom_diff_hunk.target_start_line_number == self.bottom_diff_hunk.target_end_line_number:      
            # -1 < start, = top overlap 
            marker += "<BOTTOM_DELETE>"
        elif self.bottom_diff_hunk.target_end_line_number - 1 == self.bottom_diff_hunk.target_start_line_number:
                range_end_line = self.bottom_diff_hunk.target_start_line_number
                range_end_char = self.bottom_diff_hunk.target_end_character
                if range_end_char == 0:
                    range_end_char = len(self.target_file_lines[range_end_line-1]) - 1

        region_range = [range_start_line, range_start_char, range_end_line, range_end_char]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, candidate_region_range)
        if fixed_character_range != None:
            candidate_region_range = fixed_character_range
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
        candidate_region_top_bottom_with_changed_lines.append(candidate_region)

        return candidate_region_top_bottom_with_changed_lines

    def top_overlap(self, bottom_last_unchanged_line):
        candidate_region_top_with_changed_lines = []

        # Expected candidate region: top_diff_hunk + searched no changed ranges
        marker = f"<{self.algorithm}><TOP_OVERLAP>"
        top_hunk_start_line = self.top_diff_hunk.target_start_line_number
        top_hunk_start_character = self.top_diff_hunk.target_start_character
        end_char = self.interest_character_range.characters_end_idx

        if top_hunk_start_line == self.top_diff_hunk.target_end_line_number:   
            top_hunk_start_line += 1   
            top_hunk_start_character = self.interest_character_range.characters_start_idx
            marker += "<TOP_DELETE>"
        
        region_range = [top_hunk_start_line, top_hunk_start_character, bottom_last_unchanged_line, end_char]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, candidate_region_range)
        if fixed_character_range != None:
            candidate_region_range = fixed_character_range
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
        candidate_region_top_with_changed_lines.append(candidate_region)

        return candidate_region_top_with_changed_lines
    
    def bottom_overlap(self, top_1st_unchanged_line):
        candidate_region_bottom_with_changed_lines = []

        # Expected candidate region: searched no changed ranges + bottom_diff_hunk
        marker = "<BOTTOM_OVERLAP>"
        end_line = self.bottom_diff_hunk.target_end_line_number - 1
        characters_end_idx = self.bottom_diff_hunk.target_end_character
        start_char = self.interest_character_range.characters_start_idx

        if self.bottom_diff_hunk.target_end_line_number == self.bottom_diff_hunk.target_start_line_number:
            # current hunk is empty
            # update end line/char indices
            end_line = self.bottom_diff_hunk.target_end_line_number
            characters_end_idx = len(self.target_file_lines[end_line-1]) - 1
            marker += "<EMPTY>"
        
        region_range = [top_1st_unchanged_line, start_char, end_line, characters_end_idx]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, candidate_region_range)
        if fixed_character_range != None:
            candidate_region_range = fixed_character_range
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
        candidate_region_bottom_with_changed_lines.append(candidate_region)
        
        return candidate_region_bottom_with_changed_lines

    def cover_changed_lines_in_between(self):
        '''
        Here the interest_character_range has the following structure:
         * 1. unchanged lines
         * 2. changed lines
         * 3. unchanged lines
        The changed lines part can be one or more, 
        but the first part and the last part, should always be unchanged lines.

        Search to map the part 1 and 3, and concatenate the results to cover part 2.
        '''

        candidate_region_cover_changed_lines = []

        # Identify the first and the last unchanged line number
        first_unchanged_line, last_unchanged_line = self.get_first_and_last_unchanged_line_numbers(self.middle_diff_hunks)

        # character level
        marker = "<COVER_IN_BETWEEN>"
        region_range = [first_unchanged_line, self.interest_character_range.characters_start_idx,
                        last_unchanged_line, self.interest_character_range.characters_end_idx]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, candidate_region_range)
        if fixed_character_range != None:
            candidate_region_range = fixed_character_range
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
        candidate_region_cover_changed_lines.append(candidate_region)
        
        return candidate_region_cover_changed_lines

    def get_first_and_last_unchanged_line_numbers(self, specified_diff_hunks, first=True, last=True):
        '''
        Get all the no changed line numbers in target commit.
        eg,. source: [15, 5, 18, 5]  -->  target: [18, 5, 21, 5]. @@ -16,2  +19,2 @@          
            Assume that source line 16, 17 which mappes to target line 19, 20 are changed. 
            The unchanged lines in source are 15, 18. The unchanged line in target are 18, 21.
        Here aims to get the unchanged lines in target (18 and 21 in this case.).
        '''

        # get the unchanged lines in source first.
        changed_line_numbers = []
        for hunk in specified_diff_hunks:
            hunk_range = range(hunk.base_start_line_number, hunk.base_end_line_number)
            changed_line_numbers.extend(list(hunk_range))
        # changed_line_numbers can be empty
        # set a number to catch the 2 expected unchanged parts.
        # assert changed_line_numbers != []
        unchanged_line_numbers = list(set(self.interest_line_numbers) - set(changed_line_numbers))
        unchanged_line_numbers.sort()
        # if first == True and last == True: # cover lines in between
        for hunk in specified_diff_hunks:
            if hunk.base_start_line_number == hunk.base_end_line_number:
                break_point = unchanged_line_numbers.index(hunk.base_start_line_number) + 1
                unchanged_line_numbers.insert(break_point, -2)
        unchanged_num = len(unchanged_line_numbers)

        # Here start to get the unchanged line numbers in target by checking the unchanged in source.
        first_unchanged_line_in_target = None
        last_unchanged_line_in_target = None

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
            # Note: the above part is the unchanged line numbers in source.
            unchanged_len_1st = len(first_unchanged_line_numbers)
            # get the 1st change hunk to locate the unchanged line numbers in target
            first_changed_line_in_target = specified_diff_hunks[0].target_start_line_number
            first_unchanged_line_in_target = first_changed_line_in_target - unchanged_len_1st
            if first_changed_line_in_target == specified_diff_hunks[0].target_end_line_number:
                # the target hunk is empty
                first_unchanged_line_in_target += 1

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
            unchanged_len_last = len(last_unchanged_line_numbers)
            # get the 1st change hunk to locate the unchanged line numbers in target
            last_changed_line_in_target = specified_diff_hunks[-1].target_end_line_number - 1
            last_unchanged_line_in_target = last_changed_line_in_target + unchanged_len_last
            if specified_diff_hunks[-1].target_start_line_number == specified_diff_hunks[-1].target_end_line_number:
                last_unchanged_line_in_target += 1
        
        if first == True and last == True:
            return first_unchanged_line_in_target, last_unchanged_line_in_target
        elif first == True and last == False:
            return first_unchanged_line_in_target
        elif first == False and last == True:
            return last_unchanged_line_in_target

def get_character_length_of_lines(file_lines):
    lines_len_list = []
    for line in file_lines:
        lines_len_list.append(len(line))
    return lines_len_list