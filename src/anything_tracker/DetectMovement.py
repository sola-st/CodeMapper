import re
from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import get_region_characters
from anything_tracker.utils.TransferRanges import get_diff_reported_range


def split_line_and_char(line_char_list): # 2-dimension list
    # Use zip with unpacking to transpose the matrix
    columns = list(zip(*line_char_list))
    columns = [list(column) for column in columns]
    return columns

def find_pair(start_line_char_list, end_line_char_list, delta):
    '''
    match 2 list, and meet the requiements. 
    For examaple:
        list 1: [3, 5]
        list 2: [13, 18, 32]
        --> find a from list 1 and b from list 2 that a + delta = b
    '''

    start_end_pairs = []

    start_line_list, start_char_list = split_line_and_char(start_line_char_list)
    end_line_list, end_char_list = split_line_and_char(end_line_char_list)

    for i, start in enumerate(start_line_list):
        end = start + delta
        if end in end_line_list:
            j = end_line_list.index(end)
            start_end_pairs.append([start, start_char_list[i], end, end_char_list[j]])

    return start_end_pairs


class DetectMovement():
    def __init__(self, interest_character_range, source_region_characters:list, \
                fully_covered_diff_line, diffs, target_file_lines, turn_off_fine_grains:bool):
        self.interest_character_range = interest_character_range
        self.source_region_characters = source_region_characters
        self.fully_covered_diff_line = fully_covered_diff_line
        self.diffs = diffs
        self.target_file_lines = target_file_lines
        self.turn_off_fine_grains = turn_off_fine_grains
        self.moved_lines_num = len(source_region_characters)

    def get_region_indices(self):
        # get location hints from unique_target_hunk_range (the may moved to location)

        # start
        first_source_line = self.source_region_characters[0]
        # check the location of the 1st line
        # start_line_char_pairs can be or more (multi starts)
        start_line_char_pairs = self.finder_helper(first_source_line) 

        # end
        last_source_line = self.source_region_characters[-1]
        # check the last line by running helper function, laso can be one or more
        end_line_char_pairs = self.finder_helper(last_source_line)

        start_end_pairs = find_pair(start_line_char_pairs, end_line_char_pairs, self.moved_lines_num-1)
        return start_end_pairs # also can be multiple

    def finder_helper(self, source_line):
        # can be start or end.
        line_char_pairs = []
        candidate_source_line = None # can be start or end line of source region
        candidate_source_idx = None

        occur_times = "".join(self.move_hunk_lines).count(source_line)
        for num, line in zip(self.unique_hunk, self.move_hunk_lines):
            if line.strip() == source_line.strip():
                # line
                candidate_source_line = num
                # character
                if self.turn_off_fine_grains == True:
                    candidate_source_idx = 1
                else: # we always annotate region start with no whitespaces.
                    candidate_source_idx = line.index(source_line.strip()) + 1 # to start at 1

                assert candidate_source_line != None
                assert candidate_source_idx != None
                line_char_pairs.append([candidate_source_line, candidate_source_idx])

                if occur_times == 1:
                    break # the only 1 start is found
                # else: keep finding the other may_starts/ends

        return line_char_pairs

    def run(self):
        moved_lines = 0
        moved_to_range_list = []
        candidate_region_list = []

        diffs_str_tmp = "".join(self.diffs)
        substrings = [
            "\033[31m",
            "\033[31m-",  # red color removal
            "\033[m",     # color reset
            "\033[32m",
            "\033[32m+",  # green color addition
            "\033[36m"   # cyan color
        ]
        escaped_substrings = map(re.escape, substrings)
        pattern = "|".join(escaped_substrings)
        regex = re.compile(pattern)
        diffs_str = regex.sub("", diffs_str_tmp)

        diffs = self.diffs
        # check if each source line occurs in diff reposrts >= twice.
        # if yes, the line may moved to another location.
        moved_lines_check = [s for s in self.source_region_characters if diffs_str.count(s.strip()) >= 2]
        if len(moved_lines_check) == self.moved_lines_num: 
            # source lines may moved to another location
            current_hunk_range_line = None
            for s in self.source_region_characters:
                for i, diff_line in enumerate(diffs):
                    diff_line = diff_line.strip()
                    if "\033[36m" in diff_line:
                        current_hunk_range_line = diff_line
                    elif "\033[32m" in diff_line:
                        diff_line_tmp = regex.sub("", diff_line)
                        diff_line = diff_line_tmp[1:].strip()
                        if diff_line == s.strip():
                            moved_lines+=1
                            tmp = current_hunk_range_line.split(" ")
                            target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                            moved_to_range_list.append(target_hunk_range)
                            diffs = diffs[i+1:] # truncate to run faster
                            break

        unique_target_hunk_range = set(moved_to_range_list)

        if len(unique_target_hunk_range) == 1:
            self.unique_hunk = list(unique_target_hunk_range)[0]
            self.move_hunk_lines = self.target_file_lines[self.unique_hunk.start-1: self.unique_hunk.stop-1]
            # all the source region lines was moved to another and the same location
            locations = self.get_region_indices()
            if locations:
                marker = "<MOVE>"
                for loc in locations:
                    candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx = loc
                    character_range = CharacterRange([candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx])
                    candidate_characters = get_region_characters(self.target_file_lines, character_range)
                    candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, marker)
                    candidate_region_list.append(candidate_region)
        else:
            # moved to different/multiple locations
            pass
        
        return candidate_region_list

