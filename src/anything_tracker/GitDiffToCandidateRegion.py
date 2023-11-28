import subprocess
from anything_tracker.CandidateRegion import CandidateRegion


class GitDiffToCandidateRegion():
    def __init__(self, meta):
        self.repo_dir = meta.repo_dir
        self.base_commit = meta.base_commit
        self.target_commit = meta.target_commit
        self.file_path = meta.file_path
        self.interest_character_range = meta.interest_character_range # object
        self.interest_line_numbers = meta.interest_line_numbers # list

        self.diff_result = ""
        self.target_hunk_range = []
        self.target_hunk_source = [] # contains all the lines shown in the diff results

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

       # TODO think about copied files
        # If the file is deleted, the target commit [may] has no corresponding character range.
        # Why [may], the interest element may moved to another file.
        get_deleted_files_command = f"git diff --name-only --diff-filter=D {self.base_commit} {self.target_commit}"
        deleted_result = subprocess.run(get_deleted_files_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        deleted_files = deleted_result.stdout

        # Find added and modified files
        cross_file_check_command = f"git diff --name-only --diff-filter=AM {self.base_commit} {self.target_commit}"
        cross_file_check_result = subprocess.run(cross_file_check_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        need_to_check_files = cross_file_check_result.stdout

        is_cross_file_map = False
        # TODO check if the interest element may moved to another file.

        if deleted_files and self.file_path in deleted_files and is_cross_file_map == False:
            # interest element is deleted
            return None

        # If the file is renamed, we track it in the new file path.
        get_renamed_files_command = f"git diff --name-status --diff-filter=R {self.base_commit} {self.target_commit}"
        renamed_result = subprocess.run(get_renamed_files_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        renamed_files = renamed_result.stdout

        renamed_file_path = ""
        if renamed_files:
            rename_cases = renamed_files.strip().split("\n")
            for rename in rename_cases:
                # R094    src/traverse.py src/common/traverse.py
                tmp = rename.split("\t")
                if tmp[1] == self.file_path:
                    renamed_file_path = tmp[2]
                    break

        # start to get changed hunks with "git diff" command
        # TODO Consider using options, like --diff-algorithm=histogram, --color-moved=plain
        commit_diff_command = f"git diff {self.base_commit} {self.target_commit} -- {self.file_path}"
        if renamed_file_path: # rename happens
            commit_diff_command = f"git diff {self.base_commit}:{self.file_path} {self.target_commit}:{renamed_file_path}"

        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
        self.diff_result = result.stdout

        candidate_regions = self.diff_result_to_target_changed_hunk()
        return candidate_regions
        
    def diff_result_to_target_changed_hunk(self):
        '''
        Analyze diff results, return target changed hunk range map, and the changed hunk sources.
        '''
        target_hunk_mark = False
        all_covered_mark = False
        target_line_number = 0
        candidate_regions = []
        uncovered_lines = self.interest_line_numbers
        changed_line_numbers_list = self.interest_line_numbers

        diffs = self.diff_result.split("\n")
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                # eg,. @@ -168,14 +168,13 @@
                # line numbers starts at 1, step is the absolute numbers of lines.
                if target_hunk_mark == True:
                    # base_hunk_range and target_hunk_range appending done
                    candidate_region = CandidateRegion([], self.target_hunk_range, self.target_hunk_source)
                    candidate_regions.append(candidate_region)
                    self.clear()
                    if all_covered_mark == True:
                        return candidate_regions
                    else:
                        target_hunk_mark = False

                tmp = diff_line.split(" ")
                current_lines_tmp = tmp[1].lstrip("-").split(",")
                start = int(current_lines_tmp[0])
                step = int(current_lines_tmp[1])
                end = start + step + 1
                base_hunk_range = range(start, end)
                if list(set(self.interest_line_numbers) & set(base_hunk_range)):
                    # range overlap
                    target_hunk_mark =True

                    uncovered_lines = list(set(uncovered_lines) - set(base_hunk_range))
                    if uncovered_lines == []:
                        all_covered_mark = True

                    target_tmp = tmp[2].lstrip("+").split(",")
                    target_start = int(target_tmp[0])
                    target_step = int(target_tmp[1])
                    target_end = target_start + target_step + 1
                    self.target_hunk_range = range(target_start, target_end)
                    target_line_number = target_start
                else: # no overlap
                    if start + step < self.interest_line_numbers[0]:
                        # current hunk changes before the source region, unchanged lines, line number changed.
                        target_tmp = tmp[2].lstrip("+").split(",")
                        target_step = int(target_tmp[1])
                        move_steps = target_step - step
                        changed_line_numbers_list = [(num + move_steps) for num in changed_line_numbers_list]
                    
            if target_hunk_mark == True and not diff_line.startswith("@@"):
                if diff_line.startswith("-"):
                    diff_line = diff_line.replace("-", "", 1)
                elif diff_line.startswith("+"):
                    diff_line = diff_line.replace("+", "", 1)

                self.target_hunk_source.append(diff_line)
                target_line_number +=1

        if list(self.target_hunk_range):
            candidate_region = CandidateRegion([], self.target_hunk_range, self.target_hunk_source)
            candidate_regions.append(candidate_region)
            self.clear()

        if changed_line_numbers_list:
            candidate_region = CandidateRegion([], changed_line_numbers_list, "<LOCATION_HELPER>")
            candidate_regions.append(candidate_region)

        return candidate_regions
    
    def clear(self):
        self.target_hunk_range = ""
        self.target_hunk_source = []