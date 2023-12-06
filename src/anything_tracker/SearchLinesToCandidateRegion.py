from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.FineGrainedWhitespace import fine_grained_changes
from anything_tracker.utils.ReadFile import get_region_characters


class SearchLinesToCandidateRegion():
    def __init__(self, meta, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_character_range = meta.interest_character_range # class instance
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.source_region_characters= meta.source_region_characters
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
        [Totally no change]
        Scenario 5:
            no diff hunks
            --> candidate: exactly searched results
        '''

        candidate_regions = []
        self.target_lines_len_list = get_character_length_of_lines(self.target_file_lines)

        # 1) locate candidates with the help of git diff
        if self.top_diff_hunk:
            candidate_regions = self.combine_diff_and_search_ranges("top")
        elif self.bottom_diff_hunk: # Scenario 4
            candidate_regions = self.combine_diff_and_search_ranges("bottom")
        elif self.middle_diff_hunks: # Scenario 3
            candidate_regions = self.cover_changed_lines_in_between()

        # 2) locate candidates by searching exactly mapped regions
        # Scenario 5: search exactly the same content
        searched_candidate_regions = self.search_exactly_mapped_context()
        candidate_regions.extend(searched_candidate_regions)
        
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

        Search to map the unchanged lines, and concatenate the results to changed diff hunk.
        '''

        unchanged_mapped_ranges = []
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
                bottom_unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, True, False)

                # Map unchanged lines
                unchanged_lines = self.source_region_characters[-(len(bottom_unchanged_line_numbers)):]
                unchanged_str = "".join(unchanged_lines)
                unchanged_mapped_ranges = self.search_exactly_mapped_context(unchanged_str, "keep_lower_part", [self.top_diff_hunk]) 
            else:
                # Scenario 2: top diff hunk + ... + bottom diff hunk
                candidate_region_top_bottom_with_changed_lines = self.top_bottom_overlap()
                return candidate_region_top_bottom_with_changed_lines
        else: # "bottom"
            # Scenario 4
            specified_diff_hunks.append(self.bottom_diff_hunk)
            if self.middle_diff_hunks:
                specified_diff_hunks.extend(self.middle_diff_hunks)
            top_unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(specified_diff_hunks, False, True)
            unchanged_lines = self.source_region_characters[0: len(top_unchanged_line_numbers)]
            unchanged_str = "".join(unchanged_lines)
            unchanged_mapped_ranges = self.search_exactly_mapped_context(unchanged_str, "keep_upper_part", [self.bottom_diff_hunk]) 
        
        # Map the mapped unchanged line ranges with diff hunk
        if location == "top":
            candidate_region_top_with_changed_lines = self.top_overlap(unchanged_mapped_ranges)
            return candidate_region_top_with_changed_lines
        else: # "bottom"
            candidate_region_bottom_with_changed_lines =self.bottom_overlap(unchanged_mapped_ranges)
            return candidate_region_bottom_with_changed_lines
            
    def top_bottom_overlap(self):
        candidate_region_top_bottom_with_changed_lines = []

        # 5 base values
        range_start_line = self.top_diff_hunk.target_start_line_number,
        range_start_char = 1
        range_end_line = self.bottom_diff_hunk.target_end_line_number - 1
        range_end_char = len(self.target_file_lines[range_end_line-1]) - 1
        marker = "<TOP_BOTTOM_OVERLAP>"

        # update the 5 values
        # check if top hunk is a delete hunk
        if self.top_diff_hunk.target_start_line_number == self.top_diff_hunk.target_end_line_number:      
            # = bottom overlap 
            range_start_line = self.top_diff_hunk.target_start_line_number+1
            marker += "<TOP_DELETE>"

        # check if bottom hunk is a delete hunk, from non-empty lines to None.
        if self.bottom_diff_hunk.target_start_line_number == self.bottom_diff_hunk.target_end_line_number:      
            # -1 < start, = top overlap 
            marker += "<BOTTOM_DELETE>"
        elif self.bottom_diff_hunk.target_end_line_number - 1 == self.bottom_diff_hunk.target_start_line_number:
                range_end_line = self.bottom_diff_hunk.target_start_line_number
                range_end_char = len(self.target_file_lines[range_end_line-1]) - 1

        region_range = [range_start_line, range_start_char, range_end_line, range_end_char]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
        candidate_region_top_bottom_with_changed_lines.append(candidate_region)

        # fine grained
        source_1st_line_str = self.source_region_characters[0]
        candidate_1st_line_str = self.target_file_lines[range_start_line-1]
        lstrip_num, tab_del_num = fine_grained_changes(source_1st_line_str, candidate_1st_line_str)
        if lstrip_num != None or tab_del_num != None:
            marker += "<FIND_GRAINED>"
            fine_grained_range_start_char = 0
            if lstrip_num != None:
                fine_grained_range_start_char = range_start_char + lstrip_num
            if  tab_del_num != None:
                fine_grained_range_start_char = range_start_char + tab_del_num
            region_range = [range_start_line, fine_grained_range_start_char, range_end_line, range_end_char]
            candidate_region_range = CharacterRange(region_range)
            candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
            candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
            candidate_region_top_bottom_with_changed_lines.append(candidate_region)

        return candidate_region_top_bottom_with_changed_lines

    def top_overlap(self, unchanged_mapped_ranges):
        candidate_region_top_with_changed_lines = []
        # Expected candidate region: top_diff_hunk + searched no changed ranges
        for mapped_range in unchanged_mapped_ranges: # unchanged_mapped_ranges is in order, start from smaller numbers
            if self.top_diff_hunk.target_end_line_number <= mapped_range.start_line_idx:
                top_hunk_start_line_idx = self.top_diff_hunk.target_start_line_number
                region_range = [self.top_diff_hunk.target_start_line_number, 1, mapped_range.end_line_idx, mapped_range.characters_end_idx]
                marker = "<TOP_OVERLAP>"
                if self.top_diff_hunk.target_start_line_number == self.top_diff_hunk.target_end_line_number:      
                    # = no change, exactly map
                    top_hunk_start_line_idx = self.top_diff_hunk.target_start_line_number+1
                    marker += "<TOP_DELETE>"
                region_range = [top_hunk_start_line_idx, 1, mapped_range.end_line_idx, mapped_range.characters_end_idx]
                candidate_region_range = CharacterRange(region_range)
                candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
                candidate_region_top_with_changed_lines.append(candidate_region)
                # fine-grained
                # "\t" is for go, language specific
                # TODO check if there is a encode way to unify all
                source_1st_line_str = self.source_region_characters[0]
                candidate_1st_line_str = self.target_file_lines[top_hunk_start_line_idx-1]
                lstrip_num, tab_del_num = fine_grained_changes(source_1st_line_str, candidate_1st_line_str)
                if lstrip_num != None or tab_del_num != None:
                    marker += "<FIND_GRAINED>"
                    fine_grained_start_char = 0
                    if lstrip_num != None:
                        fine_grained_start_char = 1 + lstrip_num
                    if  tab_del_num != None:
                        fine_grained_start_char = 1 + tab_del_num
                    region_range = [top_hunk_start_line_idx, fine_grained_start_char, mapped_range.end_line_idx, mapped_range.characters_end_idx]
                    candidate_region_range = CharacterRange(region_range)
                    candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
                    candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, marker)
                    candidate_region_top_with_changed_lines.append(candidate_region)

                return candidate_region_top_with_changed_lines
    
    def bottom_overlap(self, unchanged_mapped_ranges):
        candidate_region_bottom_with_changed_lines = []
        # Expected candidate region: searched no changed ranges + bottom_diff_hunk
        for mapped_range in unchanged_mapped_ranges:
            if self.bottom_diff_hunk.target_start_line_number >= mapped_range.end_line_idx:
                if self.bottom_diff_hunk.target_end_line_number == self.bottom_diff_hunk.target_start_line_number:
                    # current hunk is empty
                    end_line = self.bottom_diff_hunk.target_start_line_number - 1
                    characters_end_idx = len(self.target_file_lines[end_line]) - 1
                    region_range = [mapped_range.start_line_idx, mapped_range.characters_start_idx, self.bottom_diff_hunk.target_end_line_number, characters_end_idx]
                    candidate_region_range = CharacterRange(region_range)
                    candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
                    candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, "<BOTTOM_OVERLAP_EMPTY>")
                    candidate_region_bottom_with_changed_lines.append(candidate_region)
                    return candidate_region_bottom_with_changed_lines

                if self.bottom_diff_hunk.target_end_line_number - 1 > self.bottom_diff_hunk.target_start_line_number:
                    end_line = self.bottom_diff_hunk.target_end_line_number - 1
                    characters_end_idx = len(self.target_file_lines[self.bottom_diff_hunk.target_end_line_number - 2]) - 1 # to reduce the length of "\n"
                else: # hunk range [187, 188)
                    characters_end_idx = len(self.target_file_lines[self.bottom_diff_hunk.target_start_line_number - 1]) - 1
                    end_line = self.bottom_diff_hunk.target_start_line_number
                region_range = [mapped_range.start_line_idx, mapped_range.characters_start_idx, end_line, characters_end_idx]
                candidate_region_range = CharacterRange(region_range)
                candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, "<BOTTOM_OVERLAP>")
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
        first_unchanged_line_numbers, last_unchanged_line_numbers = self.get_first_and_last_unchanged_line_numbers(self.middle_diff_hunks)

        # Map unchanged line, cover the lines in between
        first_unchanged_lines = self.source_region_characters[0:len(first_unchanged_line_numbers)]
        first_unchanged_str = "".join(first_unchanged_lines)
        last_unchanged_lines = self.source_region_characters[-(len(last_unchanged_line_numbers)):]
        last_unchanged_str = "".join(last_unchanged_lines)

        # Map the first and the last ranges
        # Requirements 1: Expected first mapped range should starts earlier than the first middle changed hunk ends.
        first_unchanged_mapped_ranges = self.search_exactly_mapped_context(first_unchanged_str, "keep_upper_part", self.middle_diff_hunks) 
        # Requirements 2: always get the closet first range (base: first middle changed hunk)
        expected_first_range = first_unchanged_mapped_ranges[-1]

        # Requirements 3: Expected last mapped range should starts later than the last middle changed hunk ends.
        last_unchanged_mapped_ranges = self.search_exactly_mapped_context(last_unchanged_str, "keep_lower_part", self.middle_diff_hunks) 
        # Requirements 4: always get the closet last range ((base: last middle changed hunk))
        expected_last_range = last_unchanged_mapped_ranges[0]

        # the line numbers in middle hunks help to locate the unchanged lines before and after
        region_range = [expected_first_range.start_line_idx, self.interest_character_range.characters_start_idx,
                        expected_last_range.end_line_idx, expected_last_range.characters_end_idx]
        candidate_region_range = CharacterRange(region_range)
        candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, "<COVER_IN_BETWEEN>")
        candidate_region_cover_changed_lines.append(candidate_region)
        
        return candidate_region_cover_changed_lines

    def get_first_and_last_unchanged_line_numbers(self, specified_diff_hunks, first=True, last=True):
        # get all the no changed line numbers
        changed_line_numbers = []
        for hunk in specified_diff_hunks:
            hunk_range = range(hunk.base_start_line_number, hunk.base_end_line_number)
            changed_line_numbers.extend(list(hunk_range))
        # actually, changed_line_numbers can be empty
        # set a number to catch the 2 expected unchanged parts.
        # assert changed_line_numbers != []
        unchanged_line_numbers = list(set(self.interest_line_numbers) - set(changed_line_numbers))
        if first == True and last == True: # cover lines in between
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

    def search_exactly_mapped_context(self, partial_source_region_str=None, truncate=None, specified_hunk=None):
        # Find the candidate_region_ranges, character level
        candidate_region_with_only_unchanged_lines = []

        source_region_character_str = ""
        target_file_lines_str = ""
        character_del = None

        if partial_source_region_str != None:
            source_region_character_str = partial_source_region_str
            target_file_lines_str = "".join(self.target_file_lines)
            if truncate == "keep_upper_part":
                first_middle_hunk_start_line_number = specified_hunk[0].target_start_line_number
                target_file_lines_str = "".join(self.target_file_lines[:first_middle_hunk_start_line_number])
            else:
                last_middle_hunk_end_line_number = specified_hunk[-1].target_end_line_number
                target_file_lines_str = "".join(self.target_file_lines[(last_middle_hunk_end_line_number - 1):])
                truncated_character = "".join(self.target_file_lines[:(last_middle_hunk_end_line_number- 1)])
                character_del = len(truncated_character)
        else:
            source_region_character_str = "".join(self.source_region_characters)
            target_file_lines_str = "".join(self.target_file_lines)

        source_region_character_str_len = len(source_region_character_str)

        indices = []
        if source_region_character_str in target_file_lines_str:
            start_index = target_file_lines_str.find(source_region_character_str)
            while start_index != -1:
                if truncate == "keep_lower_part":
                    indices.append(start_index + character_del + 1)
                    break
                else:
                    indices.append(start_index+1)
                start_index = target_file_lines_str.find(source_region_character_str, start_index + 1)
        
        if indices:
            if partial_source_region_str != None:
                unchanged_mapped_ranges = self.transfer_character_ranges(indices, source_region_character_str_len, True)
                return unchanged_mapped_ranges
            else:
                candidate_region_with_only_unchanged_lines = self.transfer_character_ranges(indices, source_region_character_str_len)

        return candidate_region_with_only_unchanged_lines

    def transfer_character_ranges(self, indices, source_region_character_str_len, partial_source_region=False):
        ''' 
        iterate all found locations, transfer pure character range to expected character range
        pure character range: the whole file as a string, records the start, end idex of interest part --> [x, y]
        expected character range: the whole file as a list --> [s, x, e, y] *class CharacterRange format*
        
        An example:
        pure character start,end index : 52, 186
        target file lines: 
            len(line 1): 48 indices[0, 47]
            len(line 2): 20 indices[48, 67]
            len(line 3): 36
            ...
        52 indicates line 2 idx 5 (start at 1)
                        line index 1, character index 4 (start at 0)
        '''

        start_character_idx = None
        end_character_idx = None
        candidate_region_with_only_unchanged_lines = []

        if partial_source_region == True:
            character_ranges = []

        target_check_start = 1
        pre_location = 0
        current_location = 0
        is_new_loop = False
        target_lines_len_list_len = len(self.target_lines_len_list) + 1

        for idx in indices:
            start_line_idx = None
            end_line_idx= None
            candidate_characters_start_idx = idx
            candidate_characters_end_idx = candidate_characters_start_idx + source_region_character_str_len - 1 # Right closed
            updated_lines_len_list = self.target_lines_len_list[target_check_start-1:]
            for line_idx, length in zip(range(target_check_start, target_lines_len_list_len), updated_lines_len_list):
                if is_new_loop == False:
                    current_location += length 
                else: 
                    is_new_loop = False
                current_location_border = current_location + 1
                if candidate_characters_start_idx in range(pre_location, current_location_border):
                    start_line_idx = line_idx
                    start_character_idx = candidate_characters_start_idx - pre_location
                if candidate_characters_end_idx in range(pre_location, current_location_border):
                    end_line_idx = line_idx
                    end_character_idx = candidate_characters_end_idx - pre_location

                pre_location = current_location

                if start_line_idx and end_line_idx:
                    region_range = [start_line_idx, start_character_idx, end_line_idx, end_character_idx]
                    candidate_region_range = CharacterRange(region_range)
                    if partial_source_region == True:
                        character_ranges.append(candidate_region_range)
                    else:
                        candidate_characters = get_region_characters(self.target_file_lines, candidate_region_range)
                        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, candidate_characters, "<LOCATION_HELPER:SEARCH>")
                        candidate_region_with_only_unchanged_lines.append(candidate_region)
                    
                    is_new_loop = True
                    pre_location -=length # back to previous
                    break

            if end_line_idx:
                target_check_start = end_line_idx # the next location may start from the line where the previous location ends.

        if partial_source_region == True:
            return character_ranges
        else:
            return candidate_region_with_only_unchanged_lines


def get_character_length_of_lines(file_lines):
    lines_len_list = []
    for line in file_lines:
        lines_len_list.append(len(line))
    return lines_len_list