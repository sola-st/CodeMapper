import subprocess

class GitDiffToTargetChangedHunk():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_line_range):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.interest_line_range = interest_line_range

        self.diff_result = ""

        # get from diff
        self.base_hunk_range = ""
        self.target_hunk_range = ""
        self.base_hunk_source = [] # contains all the lines shown in the diff results (changed + not changed)
        self.target_hunk_source = []
        # get by analyzing diff
        self.base_real_changed_line_numbers = []
        self.target_real_changed_line_numbers = []
        self.base_real_changed_hunk_source = []
        self.target_real_changed_hunk_source = []

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

        # if the file is deleted, the target commit may has no corresponding character range.
        get_deleted_files_command = f"git diff --name-only --diff-filter=D {self.base_commit} {self.target_commit}"
        deleted_result = subprocess.run(get_deleted_files_command, cwd=self.repo_dir, shell=True,
            stdout=subprocess.PIPE, universal_newlines=True)
        deleted_files = deleted_result.stdout

        if deleted_files and self.file_path in deleted_files:
            # changed hunk map is empty
            return None

        # if the file is renamed, we track it in the new file path.
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
        commit_diff_command = f"git diff {self.base_commit} {self.target_commit} -- {self.file_path}"
        if renamed_file_path: # rename happens
            commit_diff_command = f"git diff {self.base_commit}:{self.file_path} {self.target_commit}:{renamed_file_path}"

        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
        self.diff_result = result.stdout

        self.diff_result_to_target_changed_hunk()

        hunk_info = {
            "base_hunk_range" : self.base_hunk_range,
            "target_hunk_range" : self.target_hunk_range,
            "base_hunk_source" : self.base_hunk_source,
            "target_hunk_source" : self.target_hunk_source,
            "base_real_changed_line_numbers" : self.base_real_changed_line_numbers,
            "target_real_changed_line_numbers" : self.target_real_changed_line_numbers,
            "base_real_changed_hunk_source" : self.base_real_changed_hunk_source,
            "target_real_changed_hunk_source" : self.target_real_changed_hunk_source,
        }
        return hunk_info
        
    def diff_result_to_target_changed_hunk(self):
        '''
        Analyze diff results, return target changed hunk range map, and the changed hunk sources.
        '''
        target_hunk_mark = False
        base_line_number = 0
        target_line_number = 0

        diffs = self.diff_result.split("\n")
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                # eg,. @@ -168,14 +168,13 @@
                # line numbers starts at 1, step is the absolute numbers of lines.
                if target_hunk_mark == True:
                    # base_hunk_range and target_hunk_range appending done
                    return

                tmp = diff_line.split(" ")
                current_lines_tmp = tmp[1].lstrip("-").split(",")
                start = int(current_lines_tmp[0])
                step = int(current_lines_tmp[1])
                end = start + step + 1
                self.base_hunk_range = range(start, end)
                if list(set(self.interest_line_range) & set(self.base_hunk_range)):
                    # range overlap
                    target_hunk_mark =True

                    target_tmp = tmp[2].lstrip("+").split(",")
                    target_start = int(target_tmp[0])
                    target_step = int(target_tmp[1])
                    target_end = target_start + target_step + 1
                    self.target_hunk_range = range(target_start, target_end)

                    base_line_number = start
                    target_line_number = target_start
                    
            if target_hunk_mark == True and not diff_line.startswith("@@"):
                if diff_line.startswith("-"):
                    diff_line = diff_line.replace("-", "", 1) # .strip()
                    self.base_real_changed_hunk_source.append(diff_line) 
                    self.base_hunk_source.append(diff_line)
                    self.base_real_changed_line_numbers.append(base_line_number)
                    base_line_number +=1
                elif diff_line.startswith("+"):
                    diff_line = diff_line.replace("+", "", 1)
                    self.target_real_changed_hunk_source.append(diff_line)
                    self.target_hunk_source.append(diff_line)
                    self.target_real_changed_line_numbers.append(target_line_number)
                    target_line_number +=1
                else:
                    self.base_hunk_source.append(diff_line)
                    self.target_hunk_source.append(diff_line)
                    base_line_number +=1
                    target_line_number +=1
        return