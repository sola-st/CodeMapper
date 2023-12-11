import subprocess
from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.DiffHunk import DiffHunk
from anything_tracker.utils.ComputeOverlapBetween2Strings import compute_overlap
from anything_tracker.utils.FineGrainedWhitespace import fine_grained_changes
from anything_tracker.utils.ReadFile import get_region_characters


class GitDiffToCandidateRegion():
    def __init__(self, meta):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.source_region_characters = meta.source_region_characters # list
        self.interest_character_range = meta.interest_character_range # object
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.target_file_lines = meta.target_file_lines

        # for fine-grain character start and end
        self.interest_first_number = self.interest_line_numbers[0]
        self.interest_first_characters = self.source_region_characters[0]
        self.interest_last_number = self.interest_line_numbers[-1]
        self.interest_last_characters = self.source_region_characters[-1]

        self.characters_start_idx = self.interest_character_range.characters_start_idx
        self.characters_end_idx = self.interest_character_range.characters_end_idx
        
    def run_git_diff(self):
        '''
        The self.target_commit refers to a new version where you want to know where the elements you're interested in are located. 
        It can be newer or older than base_commits.

        Command: git diff commit_a commit_b -- <file_path>
            * commit_a and commit_b can be continuous or discontinuous.
            * commit_a can be newer or older than commit_b.
            * do not need to check out to the corresponding commit.
        here we run diff in a commit that newer than both a and b.
        '''
        # TODO Get back later
        # # TODO think about copied files
        # # If the file is deleted, the target commit [may] has no corresponding character range.
        # # Why [may], the interest element may moved to another file.
        # get_deleted_files_command = f"git diff --name-only --diff-filter=D {self.base_commit} {self.target_commit}"
        # deleted_result = subprocess.run(get_deleted_files_command, cwd=self.repo_dir, shell=True,
        #     stdout=subprocess.PIPE, universal_newlines=True)
        # deleted_files = deleted_result.stdout

        # # Find added and modified files
        # cross_file_check_command = f"git diff --name-only --diff-filter=AM {self.base_commit} {self.target_commit}"
        # cross_file_check_result = subprocess.run(cross_file_check_command, cwd=self.repo_dir, shell=True,
        #     stdout=subprocess.PIPE, universal_newlines=True)
        # need_to_check_files = cross_file_check_result.stdout

        # is_cross_file_map = False
        # # TODO check if the interest element may moved to another file.

        # if deleted_files and self.file_path in deleted_files and is_cross_file_map == False:
        #     # interest element is deleted
        #     return None

        # # If the file is renamed, we track it in the new file path.
        # get_renamed_files_command = f"git diff --name-status --diff-filter=R {self.base_commit} {self.target_commit}"
        # renamed_result = subprocess.run(get_renamed_files_command, cwd=self.repo_dir, shell=True,
        #     stdout=subprocess.PIPE, universal_newlines=True)
        # renamed_files = renamed_result.stdout

        # renamed_file_path = ""
        # if renamed_files:
        #     rename_cases = renamed_files.strip().split("\n")
        #     for rename in rename_cases:
        #         # R094    src/traverse.py src/common/traverse.py
        #         tmp = rename.split("\t")
        #         if tmp[1] == self.file_path:
        #             renamed_file_path = tmp[2]
        #             break

        # start to get changed hunks with "git diff" command
        # TODO Consider using options, like --diff-algorithm=histogram, --color-moved=plain
        commit_diff_command = f"git diff --color --unified=0 --word-diff-regex='\w+' {self.base_commit} {self.target_commit} -- {self.file_path}"
        # if renamed_file_path: # rename happens
        #     commit_diff_command = f"git diff {self.base_commit}:{self.file_path} {self.target_commit}:{renamed_file_path}"

        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
        diff_result = result.stdout

        candidate_regions, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = self.diff_result_to_target_changed_hunk(diff_result)
        return candidate_regions, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks
        
    def diff_result_to_target_changed_hunk(self, diff_result):
        '''
        Analyze diff results, return target changed hunk range map, and the changed hunk sources.
        '''
        # for character start and end
        candidate_character_start_idx = 0
        candidate_character_end_idx = 0
        # only run once
        candidate_character_start_idx_done = False
        candidate_character_end_idx_done = False

        # for checking changed hunk
        all_covered_mark = False
        candidate_regions = []
        top_diff_hunks = []
        middle_diff_hunks = []
        bottom_diff_hunks = []
        uncovered_lines = self.interest_line_numbers
        changed_line_numbers_list = self.interest_line_numbers # all numbers start at 1.

        self.diffs = diff_result.split("\n")
        for diff_line_num, diff_line in enumerate(self.diffs):
            diff_line = diff_line.strip()
            if "\033[36m" in diff_line:
                if all_covered_mark == True:
                    break
                # Can be in format: @@ -168,14 +168,13 @@ | @@ -233 +236 @@ | @@ -235,2 +238 @@
                # line numbers starts at 1, step is the absolute numbers of lines.
                tmp = diff_line.split(" ")
                # last_line_number is the actual line numbers, starts at 1.
                base_hunk_range, base_step, last_line_number = get_diff_reported_range(tmp[1])
                '''
                Range overlapped or not:
                 * overlap --> check how interest_line_numbers and base_hunk_range overlapped.
                 * no overlap --> help to locate the unchanged lines.
                '''
                overlapped_line_numbers = list(set(self.interest_line_numbers) & set(base_hunk_range))
                if base_hunk_range.start == base_hunk_range.stop:
                    overlapped_line_numbers = list(set(self.interest_line_numbers) & set([base_hunk_range.start]))
                    if overlapped_line_numbers:
                        overlapped_line_numbers.append(-1)
                if overlapped_line_numbers: # range overlap
                    if self.interest_first_number in overlapped_line_numbers and candidate_character_start_idx_done == False:
                        if self.characters_start_idx == 1:
                            candidate_character_start_idx = 1
                        else:
                            candidate_character_start_idx = self.fine_grained_start_and_end_character_indices(diff_line_num, base_hunk_range, True)
                        candidate_character_start_idx_done = True

                    if self.interest_last_number in overlapped_line_numbers and candidate_character_end_idx_done == False:
                        candidate_character_end_idx = self.fine_grained_start_and_end_character_indices(diff_line_num, base_hunk_range, False)
                        candidate_character_end_idx_done = True

                    base_hunk_range_list = list(base_hunk_range)
                    if base_hunk_range.start == base_hunk_range.stop:
                        base_hunk_range_list.append(base_hunk_range.start)
                    uncovered_lines = list(set(uncovered_lines) - set(base_hunk_range_list))
                    if uncovered_lines == []:
                        all_covered_mark = True
                    target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                    '''
                    check the position of the overlap: 
                     * fully covered --> candidate region
                     * top, middle, bottom of source ranges --> diff hunks
                    '''
                    if list(set(self.interest_line_numbers) - set(base_hunk_range_list)) == []: 
                        if base_hunk_range.start == base_hunk_range.stop: # no changed, bottom overlap
                            diff_hunk = DiffHunk(base_hunk_range.start, base_hunk_range.stop, 
                                             target_hunk_range.start, target_hunk_range.stop,
                                             candidate_character_start_idx, candidate_character_end_idx)
                            bottom_diff_hunks.append(diff_hunk)
                        else:
                            # fully covered by changed hunk
                            # Heuristic: set character indices as 0 and the length of the last line in target range.
                            if target_hunk_range.stop == target_hunk_range.start:
                                # source region lines are deleted
                                character_range = CharacterRange([0, 0, 0, 0])
                                candidate_region = CandidateRegion(self.interest_character_range, character_range, None, "<LOCATION_HELPER:DIFF_DELETE>")
                                candidate_regions.append(candidate_region)
                                continue

                            hunk_end = target_hunk_range.stop - 1
                            if hunk_end <= target_hunk_range.start:
                                hunk_end = target_hunk_range.start
                            marker = "<LOCATION_HELPER:DIFF_FULLY_COVER>"
                            if candidate_character_end_idx == 0:
                                candidate_character_end_idx = len(self.target_file_lines[hunk_end-1]) - 1 # to reduce the length of "\n"

                            character_range = CharacterRange([target_hunk_range.start, candidate_character_start_idx, hunk_end, candidate_character_end_idx])
                            candidate_characters = get_region_characters(self.target_file_lines, character_range)
                            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, marker)
                            candidate_regions.append(candidate_region)
                    else:
                        location = locate_changes(overlapped_line_numbers, self.interest_line_numbers)
                        diff_hunk = DiffHunk(base_hunk_range.start, base_hunk_range.stop, 
                                             target_hunk_range.start, target_hunk_range.stop,
                                             candidate_character_start_idx, candidate_character_end_idx)
                        if location == "top":
                            top_diff_hunks.append(diff_hunk)
                        elif location == "middle":
                            middle_diff_hunks.append(diff_hunk)
                        elif location == "bottom":
                            bottom_diff_hunks.append(diff_hunk)
                else: # no overlap
                    if last_line_number < self.interest_line_numbers[0]:
                        # current hunk changes before the source region, unchanged lines, update changed line numbers.
                        target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                        move_steps = target_step - base_step
                        changed_line_numbers_list = [(num + move_steps) for num in changed_line_numbers_list]

        if changed_line_numbers_list != self.interest_line_numbers and \
                not candidate_regions and \
                not top_diff_hunks and \
                not middle_diff_hunks and \
                not bottom_diff_hunks:
            # No changed lines, with only line number changed.
            character_range = CharacterRange([changed_line_numbers_list[0], self.characters_start_idx, changed_line_numbers_list[-1], self.characters_end_idx])
            candidate_characters = get_region_characters(self.target_file_lines, character_range)
            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, "<LOCATION_HELPER:DIFF_NO_CHANGE>")
            candidate_regions.append(candidate_region)

        return candidate_regions, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks
    
    def fine_grained_start_and_end_character_indices(self, diff_line_num, base_hunk_range, is_start):
        '''
        compute and return the fine-grained index
         * 31m red -> deleted 
         * 32m green --> add
        eg,. diff identifies line 12 involves in changed hunk, and let's assume no whitespaces at the beginning of line 12.
            the source region is start from line 12, character 20.
            without this function, the candidate region will starts from character 1
            with this function, it will be more closer to 12.
        '''

        specified_line_number_idx = None
        base_list:list = list(base_hunk_range)
        if base_list == []: # delete hunk
            specified_line_number_idx = 0
        else:
            if is_start == True:
                specified_line_number_idx = base_list.index(self.interest_first_number)
            else:
                specified_line_number_idx = base_list.index(self.interest_last_number)
        interest_first_line_characters_in_diff = self.diffs[diff_line_num + specified_line_number_idx + 1]
        splits = interest_first_line_characters_in_diff.split("\033")
        splits = [s for s in splits if not s == "[m"]
        for i, s in enumerate(splits):
            if s.startswith("[m"):
                splits[i] = s[2:]

        candidate_color_character_idx = None
        source_pre_characters_len = 0
        candidate_pre_characters_len = 0
        pre_1_s = ""
        pre_1_s_len = 0
        pre_in_color = False
        fit_condition = False
        
        for i, s in enumerate(splits):
            if is_start == True:
                if source_pre_characters_len >= self.characters_start_idx: # the closest one before the source start
                    candidate_color_character_idx = self.fine_grained_return_helper( 
                            pre_in_color, pre_1_s, pre_1_s_len, is_start, candidate_pre_characters_len) 
            else:
                if source_pre_characters_len == self.characters_end_idx:
                    s_len = len(s)
                    if "[32m" in s:
                        s_len = len(s[6:-2])
                    candidate_color_character_idx = candidate_pre_characters_len + s_len
                    return candidate_color_character_idx
                elif source_pre_characters_len > self.characters_end_idx:
                    fit_condition = True
                    if "[32m" in s:
                        ns = s[6:-2]
                        ns_len = len(ns)
                        candidate_pre_characters_len += ns_len
                        in_color = True
                        candidate_color_character_idx = self.fine_grained_return_helper( 
                                in_color, ns, ns_len, is_start, candidate_pre_characters_len)
                    else:
                        candidate_color_character_idx = candidate_pre_characters_len + len(s)

            if candidate_color_character_idx != None:
                return candidate_color_character_idx

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
            if pre_in_color == True:
                candidate_color_character_idx = candidate_pre_characters_len
            else:
                overlapped_num = compute_overlap(self.interest_last_characters, pre_1_s)
                candidate_color_character_idx = candidate_pre_characters_len - pre_1_s_len + overlapped_num

            return candidate_color_character_idx

    def fine_grained_return_helper(self, pre_in_color, pre_1_s, pre_1_s_len, is_start, candidate_pre_characters_len, updated=False):
        candidate_color_character_idx = 0

        if is_start == True: # start line
            if pre_in_color == False:
                overlapped_num = compute_overlap(pre_1_s, self.interest_first_characters) # string end vs. string start
                candidate_color_character_idx = candidate_pre_characters_len - overlapped_num + 1 # starts at 1
            else:
                candidate_color_character_idx = candidate_pre_characters_len + 1 
        else: # end line
            # TODO move in color part
            if pre_in_color == False:
                overlapped_num = compute_overlap(self.interest_last_characters, pre_1_s)
                candidate_color_character_idx = candidate_pre_characters_len - (pre_1_s_len - overlapped_num) + 1

        return candidate_color_character_idx

def locate_changes(overlapped_line_numbers, interest_line_numbers):
    location = None

    after_record_line = False
    if overlapped_line_numbers[-1] == -1: # no lines in diff base hunks
        after_record_line = True
        overlapped_line_numbers = overlapped_line_numbers[:-1]
    overlapped_line_numbers.sort()
    overlapped_num = len(overlapped_line_numbers)
    if interest_line_numbers[:overlapped_num] == overlapped_line_numbers:
        if after_record_line == True:
            location = "middle"
        else:
            location = "top"
    elif interest_line_numbers[-overlapped_num:] == overlapped_line_numbers:
        # TODO after_record_line?
        location = "bottom"
    else:
        location = "middle"

    return location

def get_diff_reported_range(meta_range, base=True):
    '''
    Get range from diff results:
    Input: 23,4  or  23
    Return: 
        * a range [ ) : end is not covered
        * step, 4 and 0 in the input examples, respectively
        * start+step, that is the line number of last line in base hunk.
    '''

    start = None
    step = None
    end = None
    reported_range = None

    sep = "+"
    if base == True:
        sep = "-"

    if "," in meta_range:
        tmp = meta_range.lstrip(sep).split(",")
        start = int(tmp[0])
        step = int(tmp[1]) 
    else:
        start = int(meta_range.lstrip(sep))
        step = 1
    end = start + step

    reported_range = range(start, end) # [x, y)

    if base == True:
        return reported_range, step, end-1
    else:
        return reported_range, step