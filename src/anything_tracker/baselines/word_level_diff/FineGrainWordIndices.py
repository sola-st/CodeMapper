from anything_tracker.utils.ComputeOverlapBetween2Strings import compute_overlap
from anything_tracker.utils.FineGrainedWhitespace import count_leading_whitespace


class FineGrainWordIndices():
    def __init__(self, target_file_lines, diffs, diff_line_num, base_hunk_range, target_hunk_range, 
                character_idx, interest_line_number, interest_line_characters, is_start):
        self.target_file_lines = target_file_lines
        self.diffs = diffs
        self.diff_line_num = diff_line_num
        self.base_hunk_range = base_hunk_range
        self.target_hunk_range = target_hunk_range
        # can be first line or last line
        self.character_idx = character_idx
        self.interest_line_number = interest_line_number
        self.interest_line_characters = interest_line_characters 
        self.is_start = is_start # true: start line/character; false: end line/character
    
    def get_partial_diff_hunk(self):
        diff_len = len(self.diffs)
        if self.is_start == True:
            # compute the to-check range start
            range_start = self.diff_line_num + 1
            if range_start >= diff_len:
                range_start = diff_len - 1
            start_line = self.diffs[range_start]
            while "[36m" in start_line or start_line.strip() == "":
                range_start -= 1
                start_line = self.diffs[range_start]
            return start_line
        else:
            range_end = None
            partial_diffs = self.diffs[self.diff_line_num+1:]
            for delta, diff_line in enumerate(partial_diffs):
                if "[36m" in diff_line: # @@ hunk ranges @@ line
                    range_end = self.diff_line_num + delta
                    break
            # compute the to-check range end
            if range_end == None or range_end > diff_len:
                range_end = diff_len - 1

            assert range_end != None
            end_line = self.diffs[range_end]
            while "[36m" in end_line or end_line.strip() == "":
                range_end -= 1
                end_line = self.diffs[range_end]
            return end_line

    def fine_grained_line_character_indices(self): 
        identified_diff_line = self.get_partial_diff_hunk()
        if not "[31m" in identified_diff_line:
            return None
        splits = identified_diff_line.split("\033")
        splits = [s for s in splits if not s == "[m"]
        for i, s in enumerate(splits):
            if s.startswith("[m"):
                splits[i] = s[2:]

        # fine grained character index
        fine_grained_character_idx = None # to return
        source_pre_characters_len = 0
        candidate_pre_characters_len = 0
        pre_1_s = ""
        pre_1_s_len = 0
        pre_in_color = False # in color: add(green) or delete(red); not in color: no change
        fit_condition = False # False: the condition is not fitted until the last iteration
        
        '''
        difference between start and end:
         * start: [candidate_pre_characters is added, focus on previous] 
                do not have to add the candidate after the source fit the >= condition
                finally return: 
                    the candidate_pre_characters_len (when source_pre_characters_len is fitted) + overlapped leading character nums
         * end: [add the failed to add candidate_pre_characters, focus on current] 
                add the candidate after the source fit the >= condition, and then compute overlaps at the end.
                finally return: 
                    the candidate_pre_characters_len (when source_pre_characters_len is fitted) + 
                    failed to add candidate_pre_characters + overlapped ending character nums
        '''
        for i, s in enumerate(splits):
            if self.is_start == True:
                if source_pre_characters_len >= self.character_idx: # the closest one before the source start
                    if i == 1 and pre_in_color == False:
                        # the fine_grained_character_idx locates in the first *unchanged* split.
                        fine_grained_character_idx = self.character_idx
                    else: 
                        fine_grained_character_idx = candidate_pre_characters_len + 1 
            else:
                if source_pre_characters_len >= self.character_idx:
                    fit_condition = True
                    ns = s[6:-2]
                    fine_grained_character_idx = candidate_pre_characters_len + len(ns)
                    
            if fine_grained_character_idx != None:
                return fine_grained_character_idx

            if "[31m" in s: # delete. eg,.[31m[-0.10.11-]
                pre_1_s = s[6:-2]
                pre_1_s_len = len(pre_1_s)
                source_pre_characters_len += pre_1_s_len
                pre_in_color = True
            elif "[32m" in s: # add. eg,. [32m{+0.10.12+}
                pre_1_s = s[6:-2]
                pre_1_s_len = len(pre_1_s)
                candidate_pre_characters_len += pre_1_s_len
                pre_in_color = True
            else:
                pre_1_s = s
                pre_1_s_len = len(s)
                source_pre_characters_len += pre_1_s_len
                candidate_pre_characters_len += pre_1_s_len
                pre_in_color = False

        if fit_condition == False:
            if self.is_start == True:
                fine_grained_character_idx = candidate_pre_characters_len - pre_1_s_len + 1
            else:
                fine_grained_character_idx = candidate_pre_characters_len

            return fine_grained_character_idx

    def fine_grained_return_helper(self, s, s_len, candidate_pre_characters_len):
        fine_grained_character_idx = 0

        if self.is_start == True: # start line
            overlapped_num = compute_overlap(s, self.interest_line_characters) # string end vs. string start
            fine_grained_character_idx = candidate_pre_characters_len - overlapped_num + 1 # starts at 1
            if fine_grained_character_idx < 1:
                fine_grained_character_idx = candidate_pre_characters_len + 1
        else: # end line
            overlapped_num = compute_overlap(self.interest_line_characters, s)
            fine_grained_character_idx = candidate_pre_characters_len - (s_len - overlapped_num)

        return fine_grained_character_idx