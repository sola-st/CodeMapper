import re
import time
from anything_tracker.utils.ComputeOverlapBetween2Strings import compute_overlap


class FineGrainLineCharacterIndices():
    def __init__(self, target_file_lines, diffs, diff_line_num, base_hunk_range, target_hunk_range, 
                character_idx, interest_line_number, interest_line_characters, 
                is_start, check_if_region_deleted=False):
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
        self.check_if_region_deleted = check_if_region_deleted
        self.special_chars = "!@#$%^&*()_[]{};/<>?\|`~'"
        self.region_deleted = False # to return
    
    def get_partial_diff_hunk(self, specified_line_number_idx):
        '''
        Due to the mis-report in git diff, this function somewhat is not reliable.
        max_len = max(len(base_list), self.target_hunk_range.stop - self.target_hunk_range.start)
        range_end = range_start + max_len # this end is not exactly the end of changed hunk, indeed >=.

        To handle thge mis-report, like the several line displayed in one line issure of diff report.
            eg,. deleted 3 lines, but only display as 1 line in diff report.
        source_words : Break the source line charcters into words and check if all of them are in the detected start/end line.
        '''

        diff_len = len(self.diffs)
        # compute the to-check range start, diff_line_num and specified_line_number_idx start at 0, 
        range_start = self.diff_line_num + specified_line_number_idx + 1
        if range_start >= diff_len:
            range_start = diff_len - 1
        init_range_start = range_start
        start_line = self.diffs[range_start]
        tmp_records = []
        interest_in_diff = []
        interest_in_diff = [w for w in self.source_words if w not in start_line]
        tmp_records.append(len(interest_in_diff))
        while "[36m" in start_line or start_line.strip() == "" or interest_in_diff:
            if range_start > self.diff_line_num + 1:
                range_start -= 1
                start_line = self.diffs[range_start]
                interest_in_diff = [w for w in self.source_words if w not in start_line]
                tmp_records.append(len(interest_in_diff))
            else:
                starts = list(range(self.diff_line_num + 1, init_range_start + 1))
                starts.reverse()
                backup_idx = tmp_records.index(min(tmp_records))
                range_start = starts[backup_idx]
                start_line = self.diffs[range_start]
                break
        
        range_end = None
        partial_diffs = self.diffs[self.diff_line_num+1:] # +1 to skip the current @@ line
        for delta, diff_line in enumerate(partial_diffs):
            if "[36m" in diff_line: # @@ hunk ranges @@ line
                range_end = self.diff_line_num + delta # the idx of end, an idx before the @@ line
                break
        # compute the to-check range end
        if range_end == None:
            range_end = diff_len - 1
        init_range_end = range_end

        end_line = self.diffs[range_end] 
        tmp_records = []
        interest_in_diff = []
        interest_in_diff = [w for w in self.source_words if w not in end_line]
        tmp_records.append(len(interest_in_diff))
        while "[36m" in end_line or start_line.strip() == "" or interest_in_diff:
            if range_end > range_start:
                range_end -= 1
                end_line = self.diffs[range_end]
                interest_in_diff = [w for w in self.source_words if w not in end_line]
                tmp_records.append(len(interest_in_diff))
            else:
                ends = list(range(range_end, init_range_end + 1))
                ends.reverse()
                backup_idx = tmp_records.index(min(tmp_records))
                range_end = ends[backup_idx]
                end_line = self.diffs[range_end]
                break

        range_end += 1 # to be an open border
        assert range_end != None
        identified_diff_line = None
        if self.is_start == True:
            identified_diff_line = start_line
        else:
            identified_diff_line = end_line

        identified_diff_line, fine_grained_line_abs = self.get_line_delta(identified_diff_line)
        return range_start, range_end, identified_diff_line, fine_grained_line_abs

    def get_line_delta(self, identified_diff_line):
        the_target_lines = self.target_file_lines[self.target_hunk_range.start-1: self.target_hunk_range.stop-1]
        patterns = [
            r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])',  # ANSI escape sequences
            r'\[-',
            r'-\]',
            r'\{\+', 
            r'\+\}'
        ]
        # Combine the patterns into a single regex pattern
        combined_pattern = '|'.join(patterns)
        regex = re.compile(combined_pattern)
        identified_diff_line_no_color = regex.sub('', identified_diff_line)
        
        check_delta = None
        for delta, line in enumerate(the_target_lines):
            line_no_special = line
            for char in self.special_chars:
                line_no_special = line_no_special.replace(char, " ")
            target_words = line_no_special.strip().split(" ")
            check_delta = [w for w in target_words if w not in identified_diff_line_no_color]
            if check_delta == []:
                break

        fine_grained_line_abs = None
        if check_delta == []:
            fine_grained_line_abs = self.target_hunk_range.start + delta
        else:
            if self.is_start:
                fine_grained_line_abs = self.target_hunk_range.start
            else:
                fine_grained_line_abs = self.target_hunk_range.stop - 1

        return identified_diff_line, fine_grained_line_abs

    def check_intra_hunk_deletions(self, range_start, range_end):
        for i in range(range_start, range_end):
            interest_line_characters_in_diff = self.diffs[i]
            # check the intra-hunk deletions, fuzzy mapping, sometimes diff mis-display the characters
            if "\033[31" in interest_line_characters_in_diff and self.source_words[0] in interest_line_characters_in_diff: 
                # is a diff line contains deletions and the interest line may deleted
                in_diff_check = [w for w in self.source_words if w in interest_line_characters_in_diff] # first round check
                if (in_diff_check == self.source_words):
                    truncate_idx = interest_line_characters_in_diff.index(self.source_words[0])
                    # check if the last operation is deletion
                    before_interest_str = interest_line_characters_in_diff[:truncate_idx].strip() # the characters before the source region
                    before_tmp = before_interest_str.split("\033") # after the split, the  start of every substr can be [31, [32, [m
                    if before_tmp[-1].startswith("[31"): # the closet one is deletion
                        after_interest_str = interest_line_characters_in_diff[truncate_idx:].strip()
                        first_color_end_idx = after_interest_str.index("\033[m")
                        after_interest_str_shorten = after_interest_str[:first_color_end_idx] # the deleted string which may include the interest snippet
                        in_diff_check_detail = [w for w in self.source_words if w in after_interest_str_shorten] # second round check
                        if (in_diff_check_detail == self.source_words): 
                            self.region_deleted = True
                            break

    def get_first_non_totally_added_line(self):
        '''
        get the expected modified/deleted line.
        if a diff line only contains green colors, it's a newly added line, 
            not really related to the considered base line.
        
        Option 1:
         * return fine_grained_character_idx
         * also return a line_delta = real identified line - change hunk start/end line
        Option 2:
         * return the splits for further check steps
        '''

        specified_line_number_idx = None

        base_list:list = list(self.base_hunk_range)
        if base_list == []: # delete hunk
            specified_line_number_idx = 0
        else:
            specified_line_number_idx = base_list.index(self.interest_line_number)

        # remove special characters, reduce/address the fail to identified issue in git diff
        interest_line_characters_no_special_char = self.interest_line_characters
        for char in self.special_chars:
            interest_line_characters_no_special_char = interest_line_characters_no_special_char.replace(char, "")
        self.source_words = interest_line_characters_no_special_char.strip().split(" ")
                
        range_start, range_end, identified_diff_line, line_delta = self.get_partial_diff_hunk(specified_line_number_idx)

        # option 1
        if self.check_if_region_deleted == True: # only check for word level diff
            if len(self.source_words) != 1: # single word
                self.check_intra_hunk_deletions(range_start, range_end) # update the value of self.region_deleted
            return self.region_deleted
        
        # option 2, check to get the first non totally added line
        assert identified_diff_line != None
        splits = identified_diff_line.split("\033")
        splits = [s for s in splits if not s == "[m"]
        for i, s in enumerate(splits):
            if s.startswith("[m"):
                splits[i] = s[2:]
        return splits, line_delta
    
    def fine_grained_line_character_indices(self): 
        '''
        compute and return the fine-grained indices
         * 31m red -> deleted 
         * 32m green --> add
        eg,. diff identifies line 12 involves in changed hunk, and let's assume no whitespaces at the beginning of line 12.
            the source region is start from line 12, character 20.
            without this function, the candidate region will starts from character 1
            with this function, it will be closer to 12.
        '''
        refine_range_time_start = time.time()
        
        results = self.get_first_non_totally_added_line()
        if isinstance(results, bool):
            return results, time.time(), refine_range_time_start # check the intra-line deletions
        else:
            # step 1: fine grained line index, get the first non totally added line.
            splits, line_delta = results

            # step 2: fine grained character index
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
                    if source_pre_characters_len >= self.character_idx and self.source_words[0] in pre_1_s: # the closest one before the source start
                        if i == 1 and pre_in_color == False:
                            # the fine_grained_character_idx locates in the first *unchanged* split.
                            fine_grained_character_idx = self.character_idx
                        else: 
                            if pre_in_color == True:
                                fine_grained_character_idx = candidate_pre_characters_len + 1 
                            else: # changed, do not need to compute overlap
                                # focus on previous
                                fine_grained_character_idx = self.fine_grained_return_helper(
                                        pre_1_s, pre_1_s_len, candidate_pre_characters_len) 
                else:
                    if source_pre_characters_len >= self.character_idx and self.source_words[-1] in pre_1_s:
                        fit_condition = True
                        if "[32m" in s:
                            ns = s[6:-2]
                            # changed, do not need to compute overlap
                            fine_grained_character_idx = candidate_pre_characters_len + len(ns)
                        else: 
                            # add the failed to add candidate_pre_characters
                            s_len = len(s)
                            candidate_pre_characters_len += s_len
                            # focus on current
                            fine_grained_character_idx = self.fine_grained_return_helper(
                                    s, s_len, candidate_pre_characters_len)
                        
                if fine_grained_character_idx != None:
                    return fine_grained_character_idx, line_delta, time.time(), refine_range_time_start

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
                    # the candidate_pre_characters are added
                    if pre_in_color == True:
                        if "[31m" in s:
                            fine_grained_character_idx = candidate_pre_characters_len + 1
                        else:
                            fine_grained_character_idx = candidate_pre_characters_len - pre_1_s_len + 1
                    else:
                        fine_grained_character_idx = self.fine_grained_return_helper(
                                pre_1_s, pre_1_s_len, candidate_pre_characters_len)
                else:
                    if pre_in_color == True:
                            fine_grained_character_idx = candidate_pre_characters_len
                    else:
                        fine_grained_character_idx = self.fine_grained_return_helper(
                                pre_1_s, pre_1_s_len, candidate_pre_characters_len)
            
            if candidate_pre_characters_len < 1:
                fine_grained_character_idx = self.character_idx

            return fine_grained_character_idx, line_delta, time.time(), refine_range_time_start

    def fine_grained_return_helper(self, s, s_len, candidate_pre_characters_len):
        fine_grained_character_idx = 0

        if self.is_start == True: # start line
            overlapped_num = compute_overlap(s, self.interest_line_characters) # string end vs. string start
            fine_grained_character_idx = candidate_pre_characters_len + overlapped_num + 1 # starts at 1
        else: # end line
            overlapped_num = compute_overlap(self.interest_line_characters, s)
            fine_grained_character_idx = candidate_pre_characters_len - (s_len - overlapped_num)

        return fine_grained_character_idx