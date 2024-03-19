from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.utils.ReadFile import get_region_characters
from anything_tracker.utils.TransferRanges import get_diff_reported_range


class DetectMovement():
    def __init__(self, interest_character_range, source_region_characters:list, fully_covered_diff_line, diffs, target_file_lines):
        self.interest_character_range = interest_character_range
        self.source_region_characters = source_region_characters
        self.fully_covered_diff_line = fully_covered_diff_line
        self.diffs = diffs
        self.target_file_lines = target_file_lines

    def get_region_indices(self):
        lines_to_check = []
        candidate_start_line = None
        candidate_character_start_idx = None
        candidate_end_line = None
        candidate_character_end_idx = None

        first_source_line = self.source_region_characters[0]
        lines_to_check.append(first_source_line)
        if len(self.source_region_characters) > 1: # multi line
            last_source_line = self.source_region_characters[-1]
            lines_to_check.append(last_source_line)

        for source_line in lines_to_check:
            source_line = source_line.strip() # to ignore the may moving-related \tab, whitespaces
            for i, line in enumerate(self.target_file_lines):
                if line.strip() == source_line:
                    if candidate_start_line == None:
                        candidate_start_line = i
                        candidate_character_start_idx = line.index(source_line) + 1 # to start at 1
                        break
                    else:
                        candidate_end_line = i
                        candidate_character_end_idx = line.index(source_line) + len(source_line)
                        break
        assert candidate_start_line != None
        assert candidate_end_line != None
        return candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx
    
    def run(self):
        moved_lines = 0
        moved_to_range_list = []
        candidate_region_list = []

        for source_line in self.source_region_characters:
            source_line = source_line.strip() # to ignore the may moving-related \tab, whitespaces
            if source_line in self.diffs:
                # movements may exists
                current_hunk_range_line = None
                for diff_line in self.diffs:
                    diff_line = diff_line.strip()
                    if "\033[36m" in diff_line:
                        current_hunk_range_line = diff_line
                    elif "\033[32m" in diff_line and diff_line[6:-2] == source_line:
                        if current_hunk_range_line != self.fully_covered_diff_line:
                            # move
                            moved_lines+=1
                            tmp = current_hunk_range_line.split(" ")
                            target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                            moved_to_range_list.append(target_hunk_range)
                            break

        if moved_lines == len(self.source_region_characters):
            # the entire source region was moved
            unique_target_hunk_range = set(moved_to_range_list)

            if len(unique_target_hunk_range) == 1:
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

