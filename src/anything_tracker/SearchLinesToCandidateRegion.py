from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import checkout_to_read_file


class SearchLinesToCandidateRegion():
    def __init__(self, meta, related_diff_hunks):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_character_range = meta.interest_character_range # class instance
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.related_diff_hunks = related_diff_hunks # DiffHunk 

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

        start_line = str(base_file_lines[start_line_idx])

        if start_line_idx == end_line_idx: 
            # source region inside one line.
            # source region only records one line number, that is, the start and end are on the same line.
            self.source_region_characters = start_line[characters_start_idx : characters_end_idx]
        else:
            # source region covers multi-line
            # separate to 3 sections: start line, middle lines, and end line.
            # section 1: start line : the entire line is covered
            characters_in_start_line = start_line[characters_start_idx:] 
           
            # section 2: middle lines : all covered
            characters_in_middle_lines= []
            if start_line_idx + 1 != end_line_idx:
                characters_in_middle_lines = base_file_lines[start_line_idx + 1 : end_line_idx]

            # section 3: end line : [character index [0: specified_index]]
            end_line = str(base_file_lines[end_line_idx]) 
            characters_in_end_line = end_line[:characters_end_idx + 1]

            self.source_region_characters.append(characters_in_start_line) 
            self.source_region_characters.extend(characters_in_middle_lines) 
            self.source_region_characters.append(characters_in_end_line) 

    def search_maps(self):
        '''
        Get candidates by searching the exactly mapping characters in target file.
        Return a list of character ranges: candidate_regions.
        '''

        candidate_regions = []

        self.get_source_region_characters() # get self.source_region_characters
        # print(self.source_region_characters)
        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.file_path)

        if self.related_diff_hunks:
            # git diff identifies that interest_character_range includes changed lines.
            candidate_regions = self.cover_changed_lines_in_between()
        else: # search exactly the same content
            candidate_regions = self.search_exactly_mapped_context()
        
        return candidate_regions
            
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
        first_unchanged_line_numbers, last_unchanged_line_numbers = self.get_first_and_last_unchanged_line_ranges()

        # Map unchanged line, cover the lines in between
        first_unchanged_lines = self.source_region_characters[0:len(first_unchanged_line_numbers)]
        first_unchanged_str = "".join(first_unchanged_lines)
        last_unchanged_lines = self.source_region_characters[-(len(last_unchanged_line_numbers)):]
        last_unchanged_str = "".join(last_unchanged_lines)
        first_unchanged_mapped_ranges = self.search_exactly_mapped_context(first_unchanged_str) 
        last_unchanged_mapped_ranges = self.search_exactly_mapped_context(last_unchanged_str) 

        # Map the first and the last ranges
        for first_range in first_unchanged_mapped_ranges:
            if first_range.start_line_idx < self.related_diff_hunks[0].target_start_line_number:
                # Find the instance with the closest range 
                closest_last_range = min(
                    filter(lambda x: x.end_line_idx > self.related_diff_hunks[-1].target_end_line_number, last_unchanged_mapped_ranges),
                    key=lambda x: first_range.start_line_idx - x.start_line_idx,
                    default=None
                )
                character_end_index = len(self.target_file_lines[closest_last_range.end_line_idx])
                region_range = [first_range.start_line_idx, 0, closest_last_range.end_line_idx, character_end_index]
                candidate_region_range = CharacterRange(region_range)
                candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<COVER_IN_BETWEEN>")
                candidate_region_cover_changed_lines.append(candidate_region)
        
        return candidate_region_cover_changed_lines

    def get_first_and_last_unchanged_line_ranges(self):
        first_unchanged_line_numbers = [] 
        last_unchanged_line_numbers = []

        changed_line_numbers = []
        for hunk in self.related_diff_hunks:
            hunk_range = range(hunk.target_start_line_number, hunk.target_end_line_number)
            changed_line_numbers.extend(list(hunk_range))

        unchanged_line_numbers = list(set(self.interest_line_numbers) - set(changed_line_numbers))
        unchanged_num = len(unchanged_line_numbers)

        # Forward iteration, get first_unchanged_line_numbers
        for i in range(unchanged_num):
            if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] + 1:
                if first_unchanged_line_numbers:
                    break
                else:
                    first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 
            else:
                first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 

        # Backward iteration, get last_unchanged_line_numbers
        unchanged_line_numbers.reverse()
        for i in range(unchanged_num):
            if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] - 1:
                if last_unchanged_line_numbers:
                    break
                else:
                    last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i]) 
            else:
                last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i])

        assert first_unchanged_line_numbers != []
        assert last_unchanged_line_numbers != []
        return first_unchanged_line_numbers, last_unchanged_line_numbers

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
                indices.append(start_index)
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

        start_line_idx = None
        start_character_idx = None
        end_line_idx= None
        end_character_idx = None
        candidate_region_with_only_unchanged_lines = []

        if partial_source_region == True:
            character_ranges = []

        target_lines_len_list = get_character_length_of_lines(self.target_file_lines)

        target_check_start = 0
        pre_location = 0
        current_location = 0

        for idx in indices:
            candidate_characters_start_idx = idx
            candidate_characters_end_idx = candidate_characters_start_idx + source_region_character_str_len - 1 # Right closed
            for line_idx, length in enumerate(target_lines_len_list[target_check_start:]):
                current_location += length
                if not start_line_idx and (candidate_characters_start_idx in range(pre_location, current_location)):
                    start_line_idx = line_idx
                    start_character_idx = candidate_characters_start_idx - pre_location
                if not end_line_idx and (candidate_characters_end_idx in range(pre_location, current_location)):
                    end_line_idx = line_idx
                    end_character_idx = candidate_characters_end_idx - pre_location + 1
                
                if start_line_idx and end_line_idx:
                    region_range = [start_line_idx, start_character_idx, end_line_idx, end_character_idx]
                    candidate_region_range = CharacterRange(region_range)
                    if partial_source_region == True:
                        character_ranges.append(candidate_region_range)
                    else:
                        candidate_region = CandidateRegion(self.interest_character_range, candidate_region_range, "<LOCATION_HELPER:SEARCH>")
                        candidate_region_with_only_unchanged_lines.append(candidate_region)
                    break

                pre_location = current_location

            if end_line_idx != 0:
                target_check_start = end_line_idx - 1 # the next location may start from the line where the previous location ends.

        if partial_source_region == True:
            return character_ranges
        else:
            return candidate_region_with_only_unchanged_lines


def get_character_length_of_lines(file_lines):
    lines_len_list = []
    for line in file_lines:
        lines_len_list.append(len(line))
    return lines_len_list