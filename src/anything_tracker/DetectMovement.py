import re
from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import get_region_characters
from anything_tracker.utils.TransferRanges import get_diff_reported_range


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
        # get loction hints from unique_target_hunk_range
        last_source_line = "" # the 1st and the last line of source range
        is_multi = False

        first_source_line = self.source_region_characters[0]
        # lines_to_check.append(first_source_line)
        if self.moved_lines_num > 1: # multi line
            last_source_line = self.source_region_characters[-1]
            # lines_to_check.append(last_source_line)
            is_multi = True

        # get location of the moved 1st and last line in target file
        if is_multi == False:
            # start and end at the same line
            candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx = \
                    self.finder_helper(first_source_line, 0, is_multi)
        else:
            # start
            candidate_start_line, candidate_character_start_idx = self.finder_helper(first_source_line)
            # end 
            candidate_end_line, candidate_character_end_idx = self.finder_helper(last_source_line, candidate_start_line)
            
        assert candidate_start_line != None
        assert candidate_end_line != None
        return candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx
    
    def finder_helper(self, source_line, check_point=0, is_multi=True):
        # can be start otr end.
        candidate_line = None
        candidate_character_idx = None
        # only needed when the is_nulti is False
        candidate_end_line = None
        candidate_character_end_idx = None

        target_lines = self.target_file_lines
        if check_point > 0:
            target_lines = self.target_file_lines[check_point:]
            
        for i, line in enumerate(target_lines):
            if line.strip().rstrip("\n") == source_line.strip().rstrip("\n"):
                candidate_line = i+1
                if check_point > 0:
                    candidate_line += check_point

                if candidate_line in self.unique_target_hunk_line_list:
                    if check_point == 0: # computation for start line and character
                        if self.turn_off_fine_grains == True:
                            candidate_character_idx = 1
                        else:
                            # we always annotate region start with no whitespaces.
                            candidate_character_idx = line.index(source_line) + 1 # to start at 1
                    else:
                        if i+2 == self.moved_lines_num: # moved lines get thecorrect size
                            if self.turn_off_fine_grains == True:
                                candidate_character_idx = len(line)
                                if line.strip() != source_line.strip():
                                    candidate_character_idx -= 1
                            else:
                                source_line = source_line.strip()
                                candidate_character_idx = line.index(source_line) + len(source_line)

                    if is_multi == False:
                        candidate_end_line = i+1
                        if self.turn_off_fine_grains == True:
                            candidate_character_end_idx = len(line)
                            if line.strip() != source_line:
                                candidate_character_end_idx -= 1
                        else:
                            source_line = source_line.strip()
                            candidate_character_end_idx = line.index(source_line) + len(source_line)
                    break

        if is_multi == False:
            return candidate_line, candidate_character_idx, candidate_end_line, candidate_character_end_idx
        else:
            return candidate_line, candidate_character_idx

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
        moved_lines_check = [s for s in self.source_region_characters if diffs_str.count(s.strip()) >= 2]
        if len(moved_lines_check) == self.moved_lines_num:
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
                            diffs = diffs[i+1:]
                            break

        unique_target_hunk_range = set(moved_to_range_list)

        if len(unique_target_hunk_range) == 1:
            unique_hunk = list(unique_target_hunk_range)[0]
            self.unique_target_hunk_line_list = list(range(unique_hunk.start, unique_hunk.stop)) # the list is always non-empty
            # all the source region lines was moved to another and the same location
            candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx = self.get_region_indices()
            character_range = CharacterRange([candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx])
            candidate_characters = get_region_characters(self.target_file_lines, character_range)
            marker = "<MOVE>"
            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, marker)
            candidate_region_list.append(candidate_region)
        else:
            # what about moved to different places, should we allow multiple pieces of target regions
            pass
        
        return candidate_region_list

