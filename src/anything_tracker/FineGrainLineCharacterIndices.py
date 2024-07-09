from anything_tracker.utils.ComputeOverlapBetween2Strings import compute_overlap
from anything_tracker.utils.FineGrainedWhitespace import count_leading_whitespace


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
        start_line = self.diffs[range_start]
        while range_start > 0 and \
                ("[36m" in start_line or start_line.strip() == "" or [w for w in self.source_words if w not in start_line]):
            range_start -= 1
            start_line = self.diffs[range_start]
        
        range_end = None
        partial_diffs = self.diffs[self.diff_line_num+1:] # +1 to skip the current @@ line
        for delta, diff_line in enumerate(partial_diffs):
            if "[36m" in diff_line: # @@ hunk ranges @@ line
                range_end = self.diff_line_num + delta # the idx of end, an idx before the @@ line
                break
        # compute the to-check range end
        if range_end == None:
            range_end = diff_len - 1
        
        end_line = self.diffs[range_end] 
        while range_end > range_start and ("[36m" in end_line or [w for w in self.source_words if w not in end_line]):
            range_end -= 1
            end_line = self.diffs[range_end]

        range_end += 1 # to be an open border
        assert range_end != None
        return range_start, range_end
    
    def check_intra_hunk_deletions(self, range_start, range_end):
        for i in range(range_start, range_end):
            interest_line_characters_in_diff = self.diffs[i]
            # option 1: check the intra-hunk deletions, fuzzy mapping, sometimes diff misdisplay the charcters
            if "\033[32" in interest_line_characters_in_diff:
                in_diff_check = [w for w in self.source_words if w in interest_line_characters_in_diff]
                if (in_diff_check == self.source_words) and self.region_deleted == False: 
                    # the source region is not interrupted
                    truncate_idx = interest_line_characters_in_diff.index(self.source_words[0])
                    tmp = interest_line_characters_in_diff[:truncate_idx].strip() # the charcters before the source region
                    if tmp.endswith("\033[31m[-"):
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
        base_list_len = len(base_list)
        if base_list == []: # delete hunk
            specified_line_number_idx = 0
        else:
            specified_line_number_idx = base_list.index(self.interest_line_number)

        # remove special characters, reduce/address the fail to identified issue in git diff
        interest_line_characters_no_special_char = self.interest_line_characters
        special_chars = "!@#$%^&*()_[]{};/<>?\|`~'"
        for char in special_chars:
            interest_line_characters_no_special_char = interest_line_characters_no_special_char.replace(char, "")
        self.source_words = interest_line_characters_no_special_char.strip().split(" ")
                
        range_start, range_end = self.get_partial_diff_hunk(specified_line_number_idx)

        # option 1
        if self.check_if_region_deleted == True: # only check for word level diff
            if len(self.source_words) != 1: # single word
                self.check_intra_hunk_deletions(range_start, range_end) # update the value of self.region_deleted
            return self.region_deleted
        
        # option 2
        # start check to get the first non totally added line
        identified_diff_line:str = None
        splits = []
        possible_diff_lines = [] 
        line_delta = None

        for z, i in enumerate(range(range_start, range_end)):
            interest_line_characters_in_diff = self.diffs[i]
            # get the first 1) modified, or 2) no change
            if "[36m" in interest_line_characters_in_diff:
                break # diff misreport
            elif "[31m" in interest_line_characters_in_diff or \
                        ("[32" in interest_line_characters_in_diff and \
                        not (interest_line_characters_in_diff.startswith("\033[32") and interest_line_characters_in_diff.endswith("[m"))):
                identified_diff_line = interest_line_characters_in_diff
                line_delta = z
                break
            elif not "[31m" in interest_line_characters_in_diff and not "[32m" in interest_line_characters_in_diff: 
                # no color, no change
                # no_change_line_idx = self.target_hunk_range.start + specified_line_number_idx + z -1
                # no_change_line = self.target_file_lines[no_change_line_idx]
                no_change_line = interest_line_characters_in_diff
                # special case: git diff able to see the whitespaces changed, but can not see the small changes on special characters
                # eg., it cannot tell the diff with "attr.start!" and "attr.start"
                for char in special_chars:
                    no_change_line_no_special_char = no_change_line.replace(char, "")
                source_words_in_diff = [word for word in self.source_words if word in no_change_line_no_special_char]
                if self.source_words == source_words_in_diff:
                    try: # check if it is a fail to identified case
                        fine_grained_character_idx = no_change_line.index(self.interest_line_characters)
                    except: # some token changed, but git diff unable to catch it.
                        fine_grained_character_idx = None
                        if self.is_start == True:
                            check_char_num_in_line = count_leading_whitespace(no_change_line, " ")
                            check_char_num_in_source = count_leading_whitespace(self.interest_line_characters, " ")
                            fine_grained_character_idx = check_char_num_in_line - check_char_num_in_source + 1
                            if fine_grained_character_idx < 0:
                                fine_grained_character_idx = 0
                            return fine_grained_character_idx, specified_line_number_idx + 1
                        else:
                            fine_grained_character_idx = len(no_change_line)
                            if not self.interest_line_characters.endswith("\n"):
                                fine_grained_character_idx -= 1
                            return fine_grained_character_idx, base_list_len - specified_line_number_idx - 1
                
            elif "[32m" in interest_line_characters_in_diff: 
                if not interest_line_characters_in_diff.endswith("[m") or not interest_line_characters_in_diff.startswith("[32m"):
                    # added characters mixed with no change characters
                    possible_diff_lines.append([interest_line_characters_in_diff, z])
        
        # handle special cases
        if identified_diff_line == None: # add characters inside a line, all the words in source are not changed.
            # assert possible_diff_lines != []
            # select the top-1 diff lines to get splits
            if possible_diff_lines != []:
                for line_list in possible_diff_lines:
                    line= line_list[0]
                    source_words_in_diff = [word for word in self.source_words if word in line]
                    if self.source_words == source_words_in_diff:
                        # all source words are in current diff line
                        identified_diff_line = line
                        line_delta = line_list[1]
                        break
                if identified_diff_line == None: # checked all the possibilities, but still fail to get the top-1
                    # Coarse grained
                    identified_diff_line = self.diffs[self.diff_line_num + specified_line_number_idx + 1]
            else: # git diff mis-report, like base hunk with 3 line numbers, but onlt show in 2 lines.
                if line_delta == None:
                    line_delta = 0
                if self.is_start == True:
                    idx = self.diff_line_num+1
                    identified_diff_line = self.diffs[idx]
                    while len(identified_diff_line.strip()) == 0:
                        idx+=1
                        identified_diff_line = self.diffs[idx]
                        line_delta+=1
                else:
                    # identified_diff_line = self.diffs[range_end]
                    idx = range_end-1
                    identified_diff_line = self.diffs[idx]
                    while identified_diff_line.strip() == "":
                        idx-=1
                        identified_diff_line = self.diffs[idx]
                        line_delta-=1

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
        results = self.get_first_non_totally_added_line()
        if isinstance(results, bool):
            return results # check the intra-line deltions
        else:
            # step 1: fine grained line index, get the first non totally added line.
            splits, line_delta = results
            if isinstance(splits, int):
                return splits, line_delta # fine_grained_character_idx, specified_line_number_idx + 1

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
                    if source_pre_characters_len >= self.character_idx: # the closest one before the source start
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
                    if source_pre_characters_len >= self.character_idx:
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
                    return fine_grained_character_idx, line_delta

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
                        # if the color is [31, candidate_pre_characters_len can be 0, and reultsin < 0 index here
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

            return fine_grained_character_idx, line_delta

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