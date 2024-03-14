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

    def get_first_last_line(self):
        specified_line_number_idx = None # source range start or end line number

        base_list:list = list(self.base_hunk_range)
        if base_list == []: # delete hunk
            specified_line_number_idx = 0
        else:
            specified_line_number_idx = base_list.index(self.interest_line_number)
                
        identified_diff_line:str = None
        splits = []
        range_start = self.diff_line_num + specified_line_number_idx + 1
        diff_len = len(self.diffs)
        if range_start >= diff_len:
            range_start = diff_len - 1
        start_line = self.diffs[range_start]
        while "[36m" in start_line or start_line.strip() == "":
            range_start -= 1
            start_line = self.diffs[range_start]

        identified_diff_line = self.diffs[range_start]
        splits = identified_diff_line.split("\033")
        splits = [s for s in splits if not s == "[m"]
        for i, s in enumerate(splits):
            if s.startswith("[m"):
                splits[i] = s[2:]
        return splits
    
    def fine_grained_word_indices(self): 
        '''
        compute and return the fine-grained indices
         * 31m red -> deleted 
         * 32m green --> add
        eg,. diff identifies line 12 involves in changed hunk, and let's assume no whitespaces at the beginning of line 12.
            the source region is start from line 12, character 20.
            without this function, the candidate region will starts from character 1
            with this function, it will be closer to 12.
        '''
        splits = self.get_first_last_line()
        fine_grained_character_idx = None # to return
        source_pre_characters_len = 0
        candidate_pre_characters_len = 0
        pre_1_s = ""
        pre_1_s_len = 0
        pre_in_color = False # in color: add(green) or delete(red); not in color: no change
        fit_condition = False # False: the condition is not fitted until the last iteration
        
        for i, s in enumerate(splits):
            if self.is_start == True:
                if source_pre_characters_len >= self.character_idx: # the closest one before the source start
                    if i == 1:
                        if pre_1_s.strip() == "": # whitespaces are with no colors, even they are deleted or added.
                            fine_grained_character_idx = candidate_pre_characters_len + 1 
                        elif pre_in_color == False: 
                            # the fine_grained_character_idx locates in the first *unchanged* split.
                            fine_grained_character_idx = self.character_idx
                    else: 
                        if pre_in_color == True or pre_1_s.strip() == "":
                            fine_grained_character_idx = candidate_pre_characters_len + 1 
                        else: 
                            fine_grained_character_idx = candidate_pre_characters_len
            else:
                if source_pre_characters_len >= self.character_idx:
                    fit_condition = True
                    if "[32m" in s:
                        if source_pre_characters_len == self.character_idx:
                            ns = s[6:-2]
                            # changed, do not need to compute overlap
                            fine_grained_character_idx = candidate_pre_characters_len + len(ns)
                        else:
                            # fined grained in s.splits
                            s_splits = s[6:-2].split(" ")
                            s_splits.reverse()
                            source_pre_characters_len-=(len(s_splits)-1)
                            for p in s_splits:
                                source_pre_characters_len-=len(p)
                                if source_pre_characters_len<=self.character_idx:
                                    fine_grained_character_idx = candidate_pre_characters_len + len(p)
                    else: 
                        # add the failed to add candidate_pre_characters
                        s_len = len(s)
                        candidate_pre_characters_len += s_len
                        # focus on current
                        fine_grained_character_idx = candidate_pre_characters_len
                    
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
                if pre_in_color == True:
                    fine_grained_character_idx = candidate_pre_characters_len - pre_1_s_len + 1
                    if fine_grained_character_idx < 0:
                        fine_grained_character_idx = candidate_pre_characters_len + 1
                else:
                    fine_grained_character_idx = candidate_pre_characters_len
            else:
                if pre_in_color == True:
                    fine_grained_character_idx = candidate_pre_characters_len
                else:
                    fine_grained_character_idx = candidate_pre_characters_len + pre_1_s_len

            return fine_grained_character_idx