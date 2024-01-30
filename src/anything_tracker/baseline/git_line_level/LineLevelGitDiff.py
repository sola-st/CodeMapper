import subprocess
from anything_tracker.CandidateRegion import CandidateRegion
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.DiffHunk import DiffHunk
from anything_tracker.GitDiffToCandidateRegion import get_diff_reported_range, locate_changes
from anything_tracker.baseline.git_line_level.GitLineToCandidateRegion import BaseGitToCandidateRegion
from anything_tracker.utils.ReadFile import get_region_characters


class LineLevelGitDiff():
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
        self.interest_last_number = self.interest_line_numbers[-1]
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

        commit_diff_command = f"git diff --color --unified=0 {self.base_commit} {self.target_commit} -- {self.file_path}"

        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
                stdout = subprocess.PIPE, universal_newlines=True)
        diff_result = result.stdout

        candidate_regions, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = self.diff_result_to_target_changed_hunk(diff_result)
        if not candidate_regions:
            candidate_regions = BaseGitToCandidateRegion(self, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).get_diff_maps()
        return candidate_regions
        
    def diff_result_to_target_changed_hunk(self, diff_result):
        '''
        Analyze diff results, return target changed hunk range map, and the changed hunk sources.
        '''
        # for character start and end
        candidate_character_start_idx = 1
        candidate_character_end_idx = 0

        # for checking changed hunk
        all_covered_mark = False
        candidate_regions = []
        top_diff_hunks = []
        middle_diff_hunks = []
        bottom_diff_hunks = []
        uncovered_lines = self.interest_line_numbers
        changed_line_numbers_list = self.interest_line_numbers # all numbers start at 1.

        diffs = diff_result.split("\n")
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if "\033[36m" in diff_line:
                if all_covered_mark == True:
                    break
                # Can be in format: @@ -168,14 +168,13 @@ | @@ -233 +236 @@ | @@ -235,2 +238 @@
                # line numbers starts at 1, step is the absolute numbers of lines.
                tmp = diff_line.split(" ")
                # last_line_number is the actual line numbers, starts at 1.
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
                            candidate_character_end_idx = len(self.target_file_lines[hunk_end-1])

                            character_range = CharacterRange([candidate_start_line, candidate_character_start_idx, candidate_end_line, candidate_character_end_idx])
                            candidate_characters = get_region_characters(self.target_file_lines, character_range)
                            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, marker)
                            candidate_regions.append(candidate_region)
                    else:
                        location = locate_changes(overlapped_line_numbers, self.interest_line_numbers)
                        diff_hunk = DiffHunk(base_hunk_range.start, base_hunk_range.stop, 
                                             candidate_start_line, candidate_end_line + 1,
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
            end_line = changed_line_numbers_list[-1]
            candidate_characters = self.target_file_lines[end_line-1]
            characters_end_idx = len(candidate_characters)
            character_range = CharacterRange([changed_line_numbers_list[0], 1, end_line, characters_end_idx])
            candidate_region = CandidateRegion(self.interest_character_range, character_range, candidate_characters, "<LOCATION_HELPER:DIFF_NO_CHANGE>")
            candidate_regions.append(candidate_region)

        return candidate_regions, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks