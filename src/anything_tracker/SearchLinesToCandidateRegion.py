from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import checkout_to_read_file


class SearchLinesToCandidateRegion():
    def __init__(self, meta, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_character_range = meta.interest_character_range # class instance
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.top_diff_hunks = top_diff_hunks # DiffHunk 
        self.middle_diff_hunks = middle_diff_hunks # DiffHunk 
        self.bottom_diff_hunks = bottom_diff_hunks # DiffHunk 

        self.source_region_characters = []
        self.source_character_lens = []
        self.target_file_lines = []
    
    def get_source_region_characters(self):
        '''
        Initially get self.source_region_characters.
        '''

        base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.file_path)

        # interest_character_range: start_line, start_character, end_line, end_character
        start_line_idx = self.interest_character_range.start_line_idx
        characters_start_idx = self.interest_character_range.characters_start_idx
        end_line_idx = self.interest_character_range.end_line_idx
        characters_end_idx = self.interest_character_range.characters_end_idx

        start_line = str(base_file_lines[start_line_idx-1])

        if start_line_idx == end_line_idx: 
            # source region inside one line.
            # source region only records one line number, that is, the start and end are on the same line.
            self.source_region_characters = start_line[characters_start_idx-1 : characters_end_idx]
        else:
            # source region covers multi-line
            # separate to 3 sections: start line, middle lines, and end line.
            # section 1: start line : the entire line is covered
            characters_in_start_line = start_line[characters_start_idx-1:] 
           
            # section 2: middle lines : all covered
            characters_in_middle_lines= []
            if start_line_idx + 1 != end_line_idx:
                characters_in_middle_lines = base_file_lines[start_line_idx : end_line_idx - 1]

            # section 3: end line : [character index [0: specified_index]]
            end_line = str(base_file_lines[end_line_idx-1]) 
            characters_in_end_line = end_line[:characters_end_idx]

            self.source_region_characters.append(characters_in_start_line) 
            self.source_region_characters.extend(characters_in_middle_lines) 
            self.source_region_characters.append(characters_in_end_line) 

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

        self.get_source_region_characters() # get self.source_region_characters
        # print(self.source_region_characters)
        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.file_path)

        if self.top_diff_hunks: # Scenarios 1 and 2
            candidate_regions = self.combine_diff_and_search_ranges("top")
        elif self.bottom_diff_hunks: # Scenario 4
            candidate_regions = self.combine_diff_and_search_ranges("bottom")
        elif self.middle_diff_hunks: # Scenario 3
            candidate_regions = self.cover_changed_lines_in_between()
        else: # Scenario 5: search exactly the same content
            candidate_regions = self.search_exactly_mapped_context()
        
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
            if not self.bottom_diff_hunks:
                # Scenario 1
                specified_diff_hunks.extend(self.top_diff_hunks)
                if self.middle_diff_hunks:
                    # also remove the changed lines in middle hunk when identify the unchanged lines
                    specified_diff_hunks.extend(self.middle_diff_hunks)
                bottom_unchanged_line_numbers = self.get_first_and_last_unchanged_line_1number(specified_diff_hunks, True, False)
            else:
                # Scenario 2: top diff hunk + ... + bottom diff hunk
                candidate_region_top_bottom_with_changed_lines = []
                bottom_hunk_end_line = self.bottom_diff_hunks[0].target_end_line_number - 1
                character_end_index = len(self.target_file_lines[bottom_hunk_end_line]) - 1
                region_range = [self.top_diff_hunks[0].target_start_line_number, 1, bottom_hunk_end_line, character_end_index]
                candidate_region_range = CharacterRange(region_range)
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<TOP_BOTTOM_OVERLAP>")
                candidate_region_top_bottom_with_changed_lines.append(candidate_region)
                return candidate_region_top_bottom_with_changed_lines
            # Map unchanged lines
            unchanged_lines = self.source_region_characters[-(len(bottom_unchanged_line_numbers)):]
            unchanged_str = "".join(unchanged_lines)
            unchanged_mapped_ranges = self.search_exactly_mapped_context(unchanged_str) 
        else: # "bottom"
            # Scenario 4
            specified_diff_hunks.extend(self.bottom_diff_hunks)
            if self.middle_diff_hunks:
                specified_diff_hunks.extend(self.middle_diff_hunks)
            top_unchanged_line_numbers = self.get_first_and_last_unchanged_line_1number(specified_diff_hunks, False, True)
            unchanged_lines = self.source_region_characters[0: len(top_unchanged_line_numbers)]
            unchanged_str = "".join(unchanged_lines)
            unchanged_mapped_ranges = self.search_exactly_mapped_context(unchanged_str) 
        
        # Map the mapped unchanged line ranges with diff hunk
        if location == "top":
            candidate_region_top_with_changed_lines = []
            # Expected candidate region: top_diff_hunk + searched no changed ranges
            for diff_hunk in self.top_diff_hunks: 
                # In theory, only one top diff hunk, also only one bottom diff hunk
                for mapped_range in unchanged_mapped_ranges: # unchanged_mapped_ranges is in order, start from smaller numbers
                    if diff_hunk.target_end_line_number <= mapped_range.start_line_idx:
                        region_range = [diff_hunk.target_start_line_number, 1, mapped_range.end_line_idx, mapped_range.characters_end_idx]
                        candidate_region_range = CharacterRange(region_range)
                        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<TOP_OVERLAP>")
                        candidate_region_top_with_changed_lines.append(candidate_region)
                        return candidate_region_top_with_changed_lines
        else: # "bottom"
            candidate_region_bottom_with_changed_lines = []
            # Expected candidate region: searched no changed ranges + bottom_diff_hunk
            for diff_hunk in self.bottom_diff_hunks: 
                for mapped_range in unchanged_mapped_ranges:
                    if diff_hunk.target_start_line_number >= mapped_range.end_line_idx:
                        characters_end_idx = len(self.target_file_lines[diff_hunk.target_end_line_number - 2]) - 1 # to reduce the length of "\n"
                        region_range = [mapped_range.start_line_idx, mapped_range.characters_start_idx,
                                diff_hunk.target_end_line_number - 1, characters_end_idx]
                        candidate_region_range = CharacterRange(region_range)
                        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<BOTTOM_OVERLAP>")
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
        # TODO updated to get unchanged lines are which able to cover "no lines" in base hunk
        first_unchanged_line_numbers, last_unchanged_line_numbers = self.get_first_and_last_unchanged_line_1number(self.middle_diff_hunks)

        # Map unchanged line, cover the lines in between
        first_unchanged_lines = self.source_region_characters[0:len(first_unchanged_line_numbers)]
        first_unchanged_str = "".join(first_unchanged_lines)
        last_unchanged_lines = self.source_region_characters[-(len(last_unchanged_line_numbers)):]
        last_unchanged_str = "".join(last_unchanged_lines)
        first_unchanged_mapped_ranges = self.search_exactly_mapped_context(first_unchanged_str) 
        last_unchanged_mapped_ranges = self.search_exactly_mapped_context(last_unchanged_str) 

        # Map the first and the last ranges
        # Requirements 1: Expected first mapped range should starts earlier than the first middle changed hunk ends.
        first_middle_hunk_start_line_number = self.middle_diff_hunks[0].target_start_line_number
        updated_first_unchanged_mapped_ranges = [first_range for first_range in first_unchanged_mapped_ranges 
                                                 if first_range.end_line_idx <= first_middle_hunk_start_line_number]
        # Requirements 2: always get the closet first range (base: first middle changed hunk)
        expected_first_range = updated_first_unchanged_mapped_ranges[-1]

        # Requirements 3: Expected last mapped range should starts later than the last middle changed hunk ends.
        last_middle_hunk_end_line_number = self.middle_diff_hunks[-1].target_end_line_number
        updated_last_unchanged_mapped_ranges = [last_range for last_range in last_unchanged_mapped_ranges 
                                                 if last_range.start_line_idx >= last_middle_hunk_end_line_number]
        # Requirements 4: always get the closet last range ((base: last middle changed hunk))
        expected_last_range = updated_last_unchanged_mapped_ranges[0]

        # the line numbers in middle hunks help to locate the unchanged lines before and after
        region_range = [expected_first_range.start_line_idx, self.interest_character_range.characters_start_idx,
                        expected_last_range.end_line_idx, expected_last_range.characters_end_idx]
        candidate_region_range = CharacterRange(region_range)
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<COVER_IN_BETWEEN>")
        candidate_region_cover_changed_lines.append(candidate_region)
        
        return candidate_region_cover_changed_lines

    def get_first_and_last_unchanged_line_1number(self, specified_diff_hunks, first=True, last=True):
        # get all the no changed line numbers
        changed_line_numbers = []
        for hunk in specified_diff_hunks:
            hunk_range = range(hunk.base_start_line_number, hunk.base_end_line_number)
            changed_line_numbers.extend(list(hunk_range))
        # actually, changed_line_numbers can be empty
        # set a number to catch the 2 expected unchanged parts.
        # assert changed_line_numbers != []
        unchanged_line_numbers = list(set(self.interest_line_numbers) - set(changed_line_numbers))
        if first == True and last == True:
            if changed_line_numbers == []:
                the_1st_top_hunk = specified_diff_hunks[-1]
                the_1st_add_point = unchanged_line_numbers.index(the_1st_top_hunk.base_start_line_number) + 1
                unchanged_line_numbers.insert(the_1st_add_point, -2)
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

    def search_exactly_mapped_context(self, partial_source_region_str=None):
        # Find the candidate_region_ranges, character level
        candidate_region_with_only_unchanged_lines = []

        source_region_character_str = ""
        if partial_source_region_str != None:
            source_region_character_str = partial_source_region_str
        else:
            source_region_character_str = "".join(self.source_region_characters)

        target_file_lines_str = "".join(self.target_file_lines)
        source_region_character_str_len = len(source_region_character_str)

        indices = []
        if source_region_character_str in target_file_lines_str:
            start_index = target_file_lines_str.find(source_region_character_str)
            while start_index != -1:
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

        target_lines_len_list = get_character_length_of_lines(self.target_file_lines)

        target_check_start = 1
        pre_location = 1
        current_location = 1
        is_new_loop = False
        target_lines_len_list_len = len(target_lines_len_list) + 1

        for idx in indices:
            start_line_idx = None
            end_line_idx= None
            candidate_characters_start_idx = idx
            candidate_characters_end_idx = candidate_characters_start_idx + source_region_character_str_len - 1 # Right closed
            updated_lines_len_list = target_lines_len_list[target_check_start-1:]
            for line_idx, length in zip(range(target_check_start, target_lines_len_list_len), updated_lines_len_list):
                if is_new_loop == False:
                    current_location += length 
                else: 
                    is_new_loop = False
                current_location_border = current_location + 1
                if candidate_characters_start_idx in range(pre_location, current_location_border):
                    start_line_idx = line_idx
                    start_character_idx = candidate_characters_start_idx - pre_location + 1 # pre_location starts at 1, get the 1 back.
                if candidate_characters_end_idx in range(pre_location, current_location_border):
                    end_line_idx = line_idx
                    end_character_idx = candidate_characters_end_idx - pre_location + 1

                pre_location = current_location

                if start_line_idx and end_line_idx:
                    region_range = [start_line_idx, start_character_idx, end_line_idx, end_character_idx]
                    candidate_region_range = CharacterRange(region_range)
                    if partial_source_region == True:
                        character_ranges.append(candidate_region_range)
                    else:
                        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<LOCATION_HELPER:SEARCH>")
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