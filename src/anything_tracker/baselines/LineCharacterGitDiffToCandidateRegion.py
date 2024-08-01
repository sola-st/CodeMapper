import subprocess
import time
from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.DiffHunk import DiffHunk
from anything_tracker.baselines.word_level_diff.FineGrainWordIndices import FineGrainWordIndices
from anything_tracker.utils.ReadFile import get_region_characters
from anything_tracker.utils.TransferRanges import get_diff_reported_range


class LineCharacterGitDiffToCandidateRegion():
    def __init__(self, meta):
        self.level = meta.level
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.source_file_path = meta.source_file_path
        self.target_file_path = meta.target_file_path
        self.source_region_characters = meta.source_region_characters # list
        self.interest_character_range = meta.interest_character_range # object
        self.interest_line_numbers = meta.interest_line_numbers # list
        self.target_file_lines = meta.target_file_lines
        self.one_round_time_info = meta.one_round_time_info # object

        # for fine-grain character start and end
        self.interest_first_number = self.interest_line_numbers[0]
        self.interest_last_number = self.interest_line_numbers[-1]
        self.characters_start_idx = self.interest_character_range.characters_start_idx
        self.characters_end_idx = self.interest_character_range.characters_end_idx
        
    def run_git_diff(self, algorithm = "default"):
        '''
        The self.target_commit refers to a new version where you want to know where the elements you're interested in are located. 
        It can be newer or older than base_commits.

        Command: git diff commit_a commit_b -- <file_path>
            * commit_a and commit_b can be continuous or discontinuous.
            * commit_a can be newer or older than commit_b.
            * do not need to check out to the corresponding commit.
        here we run diff in a commit that newer than both a and b.
        '''

        # start to get changed hunks with "git diff" command
        diff_result = self.get_changed_hunks()
        candidate_regions = []
        regions = []
        diff_hunk_lists = []
        
        iteration_start_time = time.time()
        sub_candidate_regions, sub_top_diff_hunks, sub_middle_diff_hunks, sub_bottom_diff_hunks = \
                self.diff_result_to_target_changed_hunk(algorithm, diff_result)
        # empty the hunks for current round
        self.top_diff_hunks = set()
        self.middle_diff_hunks = set()
        self.bottom_diff_hunks = set()

        for sub in sub_candidate_regions:
            r = sub.candidate_region_character_range.four_element_list
            if regions == []:
                regions.append(r)
                candidate_regions.append(sub)
            else:
                if not r in regions:
                    candidate_regions.append(sub)
        # make sure the sub_middle_diff_hunks are in order (incresed)
        sorted_sub_middle_diff_hunks = sorted(list(sub_middle_diff_hunks), key=lambda obj: obj.base_start_line_number)
        diff_hunk_lists.append([algorithm, list(sub_top_diff_hunks), sorted_sub_middle_diff_hunks, list(sub_bottom_diff_hunks)])
        
        iteration_end_time = time.time()
        extract_hunks_time = f"{(iteration_end_time - iteration_start_time):.5f}"
        self.one_round_time_info.extract_hunks_time = extract_hunks_time

        return candidate_regions, diff_hunk_lists

    def get_changed_hunks(self): 
        # run only the default algorithm
        diff_command_start_time = time.time()
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        suffix = f"{self.base_commit}:{self.source_file_path} {self.target_commit}:{self.target_file_path}"
        prefix = f"git diff --ignore-space-at-eol --color --unified=0"
        if self.level == "line":
            command = f"{prefix} {suffix}"
        else:
            command = f"{prefix} --word-diff {suffix}"
        for encoding in encodings_to_try:
            try:
                result = subprocess.run(command, cwd=self.repo_dir, shell=True, encoding=encoding,
                        stdout = subprocess.PIPE, universal_newlines=True)
                diff_result = result.stdout
                break
            except UnicodeDecodeError:
                print(f"Failed to decode using, {encoding}. Subprocess")

        diff_command_end_time = time.time()
        diff_command_time = f"{(diff_command_end_time - diff_command_start_time):.5f}"
        self.one_round_time_info.diff_computation = diff_command_time

        return diff_result

    def diff_result_to_target_changed_hunk(self, algorithm, diff_result):
        '''
        Analyze diff results, return target changed hunk range map, and the changed hunk sources.
        '''

        candidate_regions = set()
        self.top_diff_hunks = set()
        self.middle_diff_hunks = set()
        self.bottom_diff_hunks = set()

        if not diff_result:
            # the source range is not changed
            candidate_characters = "".join(self.source_region_characters)
            candidate_region = CandidateRegion(self.interest_character_range, \
                    self.interest_character_range, candidate_characters, "<WHOLE_FILE_NO_CHANGE>")
            candidate_regions.add(candidate_region)
            return candidate_regions, self.top_diff_hunks, self.middle_diff_hunks, self.bottom_diff_hunks
        
        # for character start and end
        candidate_character_start_idx = 0
        candidate_character_end_idx = 0
        # only run once
        candidate_character_start_idx_done = False
        candidate_character_end_idx_done = False

        # for checking changed hunk
        all_covered_mark = False
        
        uncovered_lines = self.interest_line_numbers
        changed_line_numbers_list = self.interest_line_numbers # all numbers start at 1.

        diffs = diff_result.split("\n")
        for diff_line_num, diff_line in enumerate(diffs):
            diff_line = diff_line.strip()
            if "\033[36m" in diff_line:
                if all_covered_mark == True:
                    break
                # Can be in format: @@ -168,14 +168,13 @@ | @@ -233 +236 @@ | @@ -235,2 +238 @@
                # line numbers starts at 1, step is the absolute numbers of lines.
                tmp = diff_line.split(" ")
                # last_line_number is the abs line numbers, starts at 1.
                base_hunk_range, base_step, last_line_number = get_diff_reported_range(tmp[1])
                target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
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

                candidate_start_line = target_hunk_range.start
                candidate_end_line = target_hunk_range.stop -1
                if overlapped_line_numbers: # range overlap
                    marker = f"<{algorithm}>"
                    if self.interest_first_number in overlapped_line_numbers and candidate_character_start_idx_done == False:
                        if self.characters_start_idx == 1:
                            candidate_character_start_idx = 1
                        else:
                            if self.level == "word":
                                interest_first_line_characters = self.source_region_characters[0]
                                fine_grain_start = FineGrainWordIndices(
                                        self.target_file_lines, diffs, diff_line_num, base_hunk_range, target_hunk_range, 
                                        self.characters_start_idx, self.interest_first_number, interest_first_line_characters, True) 
                                candidate_character_start_idx_tmp = fine_grain_start.fine_grained_line_character_indices()
                                if candidate_character_start_idx_tmp != None:
                                    candidate_character_start_idx = candidate_character_start_idx_tmp
                                else:
                                    start_line = self.target_file_lines[target_hunk_range.start-1]
                                    candidate_character_start_idx = len(start_line) - len(start_line.lstrip()) + 1
                            else:
                                marker = f"{marker}"
                        candidate_character_start_idx_done = True

                    if self.interest_last_number in overlapped_line_numbers and candidate_character_end_idx_done == False:
                        if self.level == "word":
                            interest_last_line_characters = self.source_region_characters[-1]
                            fine_grain_end = FineGrainWordIndices(
                                        self.target_file_lines, diffs, diff_line_num, base_hunk_range, target_hunk_range, 
                                        self.characters_end_idx, self.interest_last_number, interest_last_line_characters, False)
                            candidate_character_end_idx_tmp = fine_grain_end.fine_grained_line_character_indices()
                            if candidate_character_end_idx_tmp != None:
                                candidate_character_end_idx = candidate_character_end_idx_tmp
                            if not marker.startswith(""):
                                marker = f"{marker}"
                        candidate_character_end_idx_done = True

                    base_hunk_range_list = list(base_hunk_range)
                    if base_hunk_range.start == base_hunk_range.stop:
                        base_hunk_range_list.append(base_hunk_range.start)
                    uncovered_lines = list(set(uncovered_lines) - set(base_hunk_range_list))
                    if uncovered_lines == []:
                        all_covered_mark = True
                    '''
                    check the position of the overlap: 
                     * fully covered --> candidate region
                     * top, middle, bottom of source ranges --> diff hunks
                    '''
                    if list(set(self.interest_line_numbers) - set(base_hunk_range_list)) == []: 
                        if base_hunk_range.start == base_hunk_range.stop: # no changed, bottom overlap
                            self.add_overlapped_hunks(base_hunk_range, candidate_start_line, candidate_end_line, overlapped_line_numbers, \
                                    candidate_character_start_idx, candidate_character_end_idx, "bottom")
                        else:
                            # fully covered by changed hunk
                            # Heuristic: set character indices as 0 and the length of the last line in target range.
                            if target_hunk_range.stop == target_hunk_range.start:
                                # source region lines are deleted
                                character_range = CharacterRange([0, 0, 0, 0])
                                candidate_region = CandidateRegion(self.interest_character_range, character_range, None, "<LOCATION_HELPER:DIFF_DELETE>")
                                candidate_regions.add(candidate_region)
                            else:
                                hunk_end = target_hunk_range.stop - 1
                                if hunk_end < target_hunk_range.start:
                                    hunk_end = target_hunk_range.start
                                marker += "<LOCATION_HELPER:DIFF_FULLY_COVER>"
                                if candidate_character_start_idx == 0:
                                    if self.level == "word":
                                        start_line = self.target_file_lines[target_hunk_range.start-1]
                                        candidate_character_start_idx = len(start_line) - len(start_line.lstrip()) + 1
                                    else:
                                        candidate_character_start_idx = 1
                                if candidate_character_end_idx == 0:
                                    candidate_character_end_idx = len(self.target_file_lines[hunk_end-1]) - 1

                                character_range = CharacterRange([candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx])
                                candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, character_range)
                                if fixed_character_range != None:
                                    character_range = fixed_character_range
                                candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, marker)
                                candidate_regions.add(candidate_region) 
                    else:
                        self.add_overlapped_hunks(base_hunk_range, candidate_start_line, candidate_end_line, overlapped_line_numbers, \
                                candidate_character_start_idx, candidate_character_end_idx)
                else: # no overlap
                    if last_line_number < self.interest_line_numbers[0]:
                        # current hunk changes before the source region, unchanged lines, update changed line numbers.
                        target_hunk_range, target_step = get_diff_reported_range(tmp[2], False)
                        move_steps = target_step - base_step
                        changed_line_numbers_list = [(num + move_steps) for num in changed_line_numbers_list]
                    elif base_hunk_range.start > self.interest_line_numbers[-1]:
                        # current (the first) changed hunk occurs after the source region, stop the hunk iteration to speed up
                        break

        if not candidate_regions and not self.top_diff_hunks and not self.middle_diff_hunks and not self.bottom_diff_hunks:
            # No changed lines, with only line number changed.
            character_range = CharacterRange([changed_line_numbers_list[0], self.characters_start_idx, changed_line_numbers_list[-1], self.characters_end_idx])
            candidate_characters, fixed_character_range = get_region_characters(self.target_file_lines, character_range)
            if fixed_character_range != None:
                character_range = fixed_character_range
            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters,  f"<{algorithm}><LOCATION_HELPER:DIFF_NO_CHANGE>")
            candidate_regions.add(candidate_region)

        return candidate_regions, self.top_diff_hunks, self.middle_diff_hunks, self.bottom_diff_hunks
    
    def add_overlapped_hunks(self, base_hunk_range, candidate_start_line, candidate_end_line, overlapped_line_numbers, \
                candidate_character_start_idx, candidate_character_end_idx, location=None):
        
        if not location: # if exists, is always "bottom"
            location = locate_changes(overlapped_line_numbers, self.interest_line_numbers)
        
        target_hunk_stare_line = self.target_file_lines[candidate_start_line-1]
        if candidate_character_start_idx < 1:
            if self.level == "word":
                candidate_character_start_idx = len(target_hunk_stare_line) - len(target_hunk_stare_line.lstrip()) + 1 # at least is 1
            else:
                candidate_character_start_idx = 1
        candidate_character_end_idx = len(self.target_file_lines[candidate_end_line-1]) - 1
        diff_hunk = DiffHunk(base_hunk_range.start, base_hunk_range.stop, 
                                candidate_start_line, candidate_end_line + 1,
                                candidate_character_start_idx, candidate_character_end_idx)

        if location == "top":
            self.top_diff_hunks.add(diff_hunk)
        elif location == "middle":
            self.middle_diff_hunks.add(diff_hunk)
        elif location == "bottom":
            self.bottom_diff_hunks.add(diff_hunk)
    
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
        location = "bottom"
    else:
        location = "middle"

    return location