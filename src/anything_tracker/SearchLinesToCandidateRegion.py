from git.repo import Repo
from anything_tracker.CandidateRegion import CandidateRegion
from os.path import join
from anything_tracker.CharacterRange import CharacterRange


class SearchLinesToCandidateRegion():
    def __init__(self, meta):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_character_range = meta.interest_character_range # class instance
        self.interest_line_numbers = meta.interest_line_numbers # list

        self.source_region_characters = []
        self.source_character_lens = []
        self.target_file_lines = []
        self.source_region_in_single_line = False
        self.no_middle_section = False

        # return
        self.candidate_regions = []

    def checkout_to_read_file(self, commit):
        repo = Repo(self.repo_dir)
        repo.git.checkout(commit, force=True)
        with open(join(self.repo_dir, self.file_path)) as f:
            file_lines= f.readlines()
        return file_lines
    
    def get_source_region_characters(self):
        '''
        Initially get self.source_region_characters.
        '''

        base_file_lines = self.checkout_to_read_file(self.base_commit)

        # interest_character_range: start_line, start_character, end_line, end_character
        start_line_idx = self.interest_character_range.start_line_idx
        characters_start_idx = self.interest_character_range.characters_start_idx
        end_line_idx = self.interest_character_range.end_line_idx
        characters_end_idx = self.interest_character_range.characters_end_idx

        start_line = str(base_file_lines[start_line_idx])

        if start_line_idx == end_line_idx: 
            # source region inside one line.
            # source region only records one line number, that is, the start and end are on the same line.
            self.source_region_characters = start_line[characters_start_idx : characters_end_idx]
            self.source_region_in_single_line = True
        else:
            # source region covers multi-line
            # separate to 3 sections: start line, middle lines, and end line.
            # section 1: start line : the entire line is covered
            characters_in_start_line = start_line[characters_start_idx:] 
           
            # section 2: middle lines : all covered
            characters_in_middle_lines= []
            if start_line_idx + 1 != end_line_idx:
                characters_in_middle_lines = base_file_lines[start_line_idx + 1 : end_line_idx]
            else: # no middle lines
                self.no_middle_section = True
            # section 3: end line : [character index [0: specified_index]]
            end_line = str(base_file_lines[end_line_idx]) 
            characters_in_end_line = end_line[:characters_end_idx + 1]

            self.source_region_characters.append(characters_in_start_line) 
            self.source_region_characters.extend(characters_in_middle_lines) 
            self.source_region_characters.append(characters_in_end_line) 

    def search_maps(self):
        '''
        Get candidates by searching the exactly mapping characters in target file.
        Return a list of character ranges.
        '''

        self.get_source_region_characters() # get self.source_region_characters
        # print(self.source_region_characters)
        self.target_file_lines = self.checkout_to_read_file(self.target_commit)

        # Find the candidate_region_ranges, character level
        if self.source_region_in_single_line == True:
            self.get_source_region_ranges_in_single_line()
        else:
            self.get_source_region_ranges_in_multi_line()

        return self.candidate_regions

    def get_character_length_of_each_source_line(self):
        for line in self.source_region_characters:
            self.source_character_lens(len(line))

    def get_source_region_ranges_in_single_line(self):
        # format of candidate_start_indices: [[12, 6], [23, 6], [38, 8], [51, 4]]
        # [12, 6]: line 12, start_idx 6
        candidate_start_indices = [[target_line_num, i] for target_line_num, target_line in enumerate(self.target_file_lines) 
                for i in range(len(target_line)) if target_line.startswith(self.source_region_characters, i)]
        # transfer to candidate region character ranges
        # here source_region_characters is a string.
        source_region_len = len(self.source_region_characters)
        for info in candidate_start_indices:
            candidate_line_number = info[0]
            candidate_region_character_start_idx = info[1]
            candidate_region_character_end_idx = candidate_region_character_start_idx + source_region_len
            candidate_region_character_range = [
                candidate_line_number, candidate_region_character_start_idx,
                candidate_line_number, candidate_region_character_end_idx]
            candidate_region_character_range_object = CharacterRange(candidate_region_character_range)
            candidate_region_character_source = self.target_file_lines[
                    candidate_line_number][candidate_region_character_start_idx:candidate_region_character_end_idx]
            assert self.source_region_characters == candidate_region_character_source
            candidate_region = CandidateRegion(self.interest_character_range, 
                    candidate_region_character_range_object, candidate_region_character_source)
            self.candidate_regions.append(candidate_region)

    def get_source_region_ranges_in_multi_line(self):
        self.start_line_candidate_character_ranges = []
        self.middle_line_mappings = []
        self.end_line_candidate_character_ranges = []
        start_line_numbers = [] # several candidates
        end_line_numbers = []

        mapped_start_line_character_start_idx = None # the mapped character start index for 1st line of source region
        mapped_end_line_character_end_idx = None # the mapped character end index for the last line of source region

        interest_start_line_num = self.interest_line_numbers[0]
        interest_end_line_num = self.interest_line_numbers[-1]
        for target_line_num, target_line in enumerate(self.target_file_lines):
            if target_line != "\n":
                for base_line_num, base_line_characters in zip(self.interest_line_numbers, self.source_region_characters):
                    # start section
                    if base_line_num == interest_start_line_num:
                        if target_line.endswith(base_line_characters):
                            target_line_len = len(target_line)
                            mapped_start_line_character_start_idx = target_line_len - len(base_line_characters)
                            end_idx = target_line_len + 1
                            # start_line_candidate_character_ranges.append([target_line_num, mapped_start_line_character_start_idx, target_line_num, end_idx])
                            self.start_line_candidate_character_ranges.append(CharacterRange([target_line_num, 
                                    mapped_start_line_character_start_idx, target_line_num, end_idx]))
                            start_line_numbers.append(target_line_num)
                    elif base_line_num < interest_end_line_num:
                        # middle section 
                        if base_line_characters == target_line:
                            self.middle_line_mappings.append([base_line_num, target_line_num])
                    else:
                        # end section : map end section at line level
                        if target_line.startswith(base_line_characters):
                            mapped_end_line_character_end_idx = len(base_line_characters) - 1
                            self.end_line_candidate_character_ranges.append(CharacterRange([target_line_num, 
                                    0, target_line_num, mapped_end_line_character_end_idx]))
                            end_line_numbers.append(target_line_num)
        # TODO get all the empty line in base file, will used to concatenate the separated lines.
        self.connect_sections_to_get_complete_candidates(start_line_numbers, end_line_numbers)

    def connect_sections_to_get_complete_candidates(self, start_line_numbers, end_line_numbers):
        '''
        4 scenarios:
        1) only one start line + only one end line.
            --> all the line in the middle should consider as a ort of the candidate region.
            --> candidate region: [the only start line, start idx, the only end line, end idex] 
        2) only one start line + multiple end lines
            --> find the nearest line numbers.
                eg,. start line 13,
                    middle lines [[14, 16], [45, 47]] --> [14, 16] is nearest range to line 13.
                    end line [17, 48, 51] --> 17 is the nearest number to line 16.
                --> candidate: from 13 to 17. Discard [45, 47], [48], and [51].
        3) only one end line + multiple start lines
            similar to 2)
        4) multiple start lines and multiple end lines.
            --> Permutations
        '''
        candidate_region_range = None
        the_only_start = False
        the_only_end = False
        no_start = False
        no_end = False

        # check if the start or end line only has 1 element.
        start_candidate_num = len(start_line_numbers)
        end_candidate_num = len(end_line_numbers)

        if start_candidate_num == 1:
            the_only_start = True
        elif start_candidate_num == 0:
            no_start = True
        if end_candidate_num == 1:
            the_only_end = True
        elif end_candidate_num == 0:
            no_end = True

        # TODO Better logic or separate the code, so far current function is too long.
        # Scenario 1: results only one reasonable candidate
        if the_only_start == True and the_only_end == True:
            the_only_start_map = self.start_line_candidate_character_ranges[0] 
            the_only_end_map = self.end_line_candidate_character_ranges[0]

            # range
            candidate_region_range = [
                the_only_start_map.start_line_idx, the_only_start_map.characters_start_idx,
                the_only_end_map.end_line_idx, the_only_end_map.characters_end_idx]
            self.append_candidate_region(candidate_region_range)

        elif the_only_start == True or the_only_end == True: 
            if self.middle_line_mappings:
                middle_line_number_groups = self.group_middle_line_mappings() # [[]]

                # Only one middle lines candidate
                if len(middle_line_number_groups) == 1:
                    middle_line_numbers = middle_line_number_groups[0] 
                    if no_start == False and no_end == False:
                        selected_start_line_number, s_idx = nearest_number(middle_line_numbers[0], start_line_numbers)
                        selected_end_line_number, e_idx = nearest_number(middle_line_numbers[-1], end_line_numbers)
                        candidate_region_range = [selected_start_line_number, 
                                                self.start_line_candidate_character_ranges[s_idx].characters_start_idx,
                                                selected_end_line_number, 
                                                self.end_line_candidate_character_ranges[e_idx].characters_end_idx]
                    # else:  # TODO check the overlap with git diff
                else:
                    if the_only_start == True: # Scenario 2
                        start_line_number = start_line_numbers[0]
                        # from start to middle
                        nearest_list = find_nearest_list(start_line_number, middle_line_number_groups, False)
                        # from middle to end
                        selected_end_line_number, e_idx = nearest_number(nearest_list[-1], nearest_list, False)
                        candidate_region_range = [start_line_number, 
                                            self.start_line_candidate_character_ranges[0].characters_start_idx,
                                            selected_end_line_number, 
                                            self.end_line_candidate_character_ranges[e_idx].characters_end_idx]
                    else: # the_only_end == True:# Scenario 3
                        end_line_number = end_line_numbers[0]
                        # from end to middle
                        nearest_list = find_nearest_list(end_line_number, middle_line_number_groups)
                        # from middle to start
                        selected_start_line_number, s_idx = nearest_number(nearest_list[0], start_line_numbers)
                        candidate_region_range = [selected_start_line_number, 
                                            self.start_line_candidate_character_ranges[s_idx].characters_start_idx,
                                            end_line_number, 
                                            self.end_line_candidate_character_ranges[0].characters_end_idx]
            else:
                if the_only_start == True: 
                    start_line_number = start_line_numbers[0]
                    if no_end == False:
                        # no middle lines, from start to end
                        selected_end_line_number, e_idx = nearest_number(start_line_number, end_line_numbers, False)
                        candidate_region_range = [start_line_number, 
                                            self.start_line_candidate_character_ranges[0].characters_start_idx,
                                            selected_end_line_number, 
                                            self.end_line_candidate_character_ranges[e_idx].characters_end_idx]
                else: # the_only_end == True:
                    end_line_number = end_line_numbers[0]
                    if no_start == False:
                        # from middle to start
                        selected_start_line_number, s_idx = nearest_number(end_line_number, start_line_numbers)
                        candidate_region_range = [selected_start_line_number, 
                                            self.start_line_candidate_character_ranges[s_idx].characters_start_idx,
                                            end_line_number, 
                                            self.end_line_candidate_character_ranges[0].characters_end_idx]
            if candidate_region_range != None:
                self.append_candidate_region(candidate_region_range)

        else: # Scenario 4
            # TODO
            print("multiple candidates")

    def append_candidate_region(self, candidate_region_range):
        # range
        candidate_region_range_object = CharacterRange(candidate_region_range)
        # source
        candidate_region_source = self.get_candidate_region_characters(candidate_region_range_object)
        # candidate region
        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range_object, candidate_region_source)
        self.candidate_regions.append(candidate_region)

    def group_middle_line_mappings(self):
        '''
        For example: middle_line_mappings: [[13, 13], [14, 14], [15, 15], [16, 16], [13, 24], [14, 25], [15, 27], [16, 30]]
        Separate to 2 groups: 
            [[13, 13], [14, 14], [15, 15], [16, 16]]
            [[13, 24], [14, 25], [15, 27], [16, 30]]
        '''
        
        # check continuity, and get subset of middle_line_mappings
        self.source_region_line_numbers = []
        self.candidate_regions = []
        self.candidate_region_line_numbers = []
        self.candidate_region_line_sources = []

        for idx_map in self.middle_line_mappings:
            # idx_map format: [[0, 1], [1, 2]]
            # [0, 1] = [base_index, target_index]
            base_line_idx = idx_map[0]
            target_line_idx = idx_map[1]
            self.source_region_line_numbers.append(base_line_idx)
            self.candidate_region_line_numbers.append(target_line_idx)
        
        # Get candidate line number list
        middle_line_number_groups = []
        is_consecutive = check_consecutive(self.candidate_region_line_numbers)
        if is_consecutive == False:
            middle_line_number_groups = self.get_sub_ranges_of_middle_mappings()
        else:
            middle_line_number_groups.append(self.candidate_region_line_numbers)
        
        return middle_line_number_groups
            
    def get_sub_ranges_of_middle_mappings(self):
        sub_range_base_line_numbers = []
        sub_range_target_line_numbers = []
        sub_ranges = []

        candidate_regions_len = len(self.candidate_region_line_numbers)
        for i in range(candidate_regions_len):
            if self.candidate_region_line_numbers[i] != self.candidate_region_line_numbers[i-1] + 1:
                if sub_range_target_line_numbers:
                    sub_ranges.append(sub_range_target_line_numbers)
                    sub_range_base_line_numbers = []
                    sub_range_target_line_numbers = []

            if sub_range_target_line_numbers:
                is_base_consecutive = check_consecutive(sub_range_base_line_numbers)
                if is_base_consecutive == False: 
                    sub_ranges.append(sub_range_target_line_numbers)
                    sub_range_base_line_numbers = []
                    sub_range_target_line_numbers = []

            sub_range_base_line_numbers.append(self.source_region_line_numbers[i])
            sub_range_target_line_numbers.append(self.candidate_region_line_numbers[i])

        return sub_ranges
    
    def get_candidate_region_characters(self, candidate_region_character_range):
        candidate_region_character_source = []

        # start 
        candidate_region_character_source.append(self.target_file_lines[candidate_region_character_range.start_line_idx
                ][candidate_region_character_range.characters_start_idx:])
        # middle
        candidate_region_character_source.extend(self.target_file_lines[
                (candidate_region_character_range.start_line_idx + 1):candidate_region_character_range.end_line_idx])
        # end
        candidate_region_character_source.append(self.target_file_lines[candidate_region_character_range.end_line_idx
                ][:candidate_region_character_range.characters_end_idx + 1])
        
        return candidate_region_character_source
    
    
def check_consecutive(number_list):
    # Return True or False
    return sorted(number_list) == list(range(min(number_list), max(number_list)+1))
    
def nearest_number(target, num_list, first_smaller=True):
    idx, nearest = min(enumerate(num_list), key=lambda x: abs(x[1] - target) if (x[1] < target) == first_smaller else float('inf'))
    return nearest, idx

def find_nearest_list(target, list_of_lists, first_smaller=True):
    element_index = 0
    comparison_operator = lambda x: x < target if first_smaller else x > target
    nearest_list = min(list_of_lists, key=lambda x: abs(x[element_index] - target) if comparison_operator(x[element_index]) else float('inf'))
    return nearest_list