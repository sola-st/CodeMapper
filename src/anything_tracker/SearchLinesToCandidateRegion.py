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
        print(self.source_region_characters)
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
        start_line_candidate_character_ranges = []
        middle_line_mappings = []
        end_line_candidate_character_ranges = []

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
                            start_line_candidate_character_ranges.append([target_line_num, mapped_start_line_character_start_idx, target_line_num, end_idx])
                    elif base_line_num < interest_end_line_num:
                        # middle section 
                        if base_line_characters == target_line:
                            middle_line_mappings.append([base_line_num, target_line_num])
                    else:
                        # end section : map end section at line level
                        if target_line.startswith(base_line_characters):
                            mapped_end_line_character_end_idx = len(target_line) - len(base_line_characters)
                            end_line_candidate_character_ranges.append([target_line_num, 0, target_line_num, mapped_end_line_character_end_idx])
        # TODO 1. get all the empty line in base file, will used to concatenate the separated lines.
        # 2. computer the occurrences of mapped lines. Basic idea, if a line only appears once, it exactly where the source region should mapped to.
        # print("s")
        # print(start_line_candidate_character_ranges)
        # print("m")
        # print(middle_line_mappings)
        # print("e")
        # print(end_line_candidate_character_ranges)
        # exit()

        ####
        # self.source_region_line_numbers = []
        # self.candidate_regions = []
        # self.candidate_region_line_numbers = []
        # self.candidate_region_line_sources = []
        # self.mappings = [] 

        # last_line_num_in_source_region = self.interest_line_numbers[-1]
        # for idx_map in line_level_mappings:
        #     # idx_map format: [[0, 1], [1, 2]]
        #     # [0, 1] = [base_index, target_index]
        #     base_line_idx = idx_map[0]
        #     target_line_idx = idx_map[1]
        #     self.source_region_line_numbers.append(base_line_idx)
        #     self.candidate_region_line_numbers.append(target_line_idx)
        #     self.candidate_region_line_sources.append(self.target_file_lines[target_line_idx])
        
        # # Get candidate ranges
        # is_consecutive = check_consecutive(self.candidate_region_line_numbers)
        # if is_consecutive == False:
        #     candidate_regions = self.get_sub_ranges()
        # else:
        #     candidate_regions = CandidateRegion(self.source_region_line_numbers, self.candidate_region_line_numbers, self.candidate_region_line_sources)

    # TODO update this function
    def get_sub_ranges(self):
        sub_range_base_line_numbers = []
        sub_range_target_line_numbers = []
        sub_range_line_sources = []
        region_line_index_map = []
        sub_range = []
        sub_ranges = []

        candidate_regions_len = len(self.candidate_region_line_numbers)
        for i in range(candidate_regions_len):
            if self.candidate_region_line_numbers[i] != self.candidate_region_line_numbers[i-1] + 1:
                if sub_range_target_line_numbers:
                    sub_range = CandidateRegion(sub_range_base_line_numbers, sub_range_target_line_numbers, sub_range_line_sources) 
                    sub_ranges.append(sub_range)
                    sub_range_base_line_numbers = []
                    sub_range_target_line_numbers = []
                    sub_range_line_sources = []
                    region_line_index_map = []
                    sub_range = []

            if sub_range_target_line_numbers:
                # is_duplicate = len(sub_range_base_line_numbers) == len(list(set(sub_range_base_line_numbers)))
                is_base_consecutive = check_consecutive(sub_range_base_line_numbers)
                if is_base_consecutive == False: 
                    sub_range = CandidateRegion(sub_range_base_line_numbers, sub_range_target_line_numbers, sub_range_line_sources) 
                    sub_ranges.append(sub_range)
                    sub_range_base_line_numbers = []
                    sub_range_target_line_numbers = []
                    sub_range_line_sources = []
                    region_line_index_map = []
                    sub_range = []

            sub_range_base_line_numbers.append(self.source_region_line_numbers[i])
            sub_range_target_line_numbers.append(self.candidate_region_line_numbers[i])
            sub_range_line_sources.append(self.candidate_region_line_sources[i])

        if sub_range_target_line_numbers:
            region_line_index_map = RegionLineIndexMap(sub_range_base_line_numbers, sub_range_target_line_numbers)
            sub_range = CandidateRegion(region_line_index_map, sub_range_line_sources)
            sub_ranges.append(sub_range)

        return sub_ranges
    
    
def check_consecutive(number_list):
    # Return True or False
    return sorted(number_list) == list(range(min(number_list), max(number_list)+1))