import subprocess

from anything_tracker.CommonFunctions import get_hunk_ranges_from_diff_line
from anything_tracker.HunkPair import HunkPair

class GetDiffResults():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_line_range):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.interest_line_range = interest_line_range

        # Get from diff
        self.base_hunk_range = ""
        self.target_hunk_range = ""
        self.base_hunk_source = [] # Contains all the lines shown in the diff results (changed + not changed)
        self.target_hunk_source = []
        # Get by analyzing diff
        self.base_real_changed_line_numbers = []
        self.target_real_changed_line_numbers = []
        self.base_real_changed_hunk_source = []
        self.target_real_changed_hunk_source = []

        self.diff_result = ""
        self.intra_file_hunk_pairs = [] # A list of objects. All hunk pairs in current file_path

    def run_git_diff(self):
        '''
        The self.target_commit refers to a new version where you want to know where the elements you're interested in are located. 
        It can be newer or older than base_commits.

        Command: git diff commit_a commit_b -- <file_path>
            * commit_a and commit_b can be continuous or discontinuous.
            * commit_a can be newer or older than commit_b.
            * do not need to check out to the corresponding commit.
        '''

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

        # Start to get changed hunks with "git diff" command
        commit_diff_command = f"git diff {self.base_commit} {self.target_commit} -- {self.file_path}"
        if renamed_file_path: # rename happens
            commit_diff_command = f"git diff {self.base_commit}:{self.file_path} {self.target_commit}:{renamed_file_path}"

        result = subprocess.run(commit_diff_command, cwd=self.repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
        self.diff_result = result.stdout

        # Update intra_file_hunk_pairs
        self.diff_result_to_changed_hunks()

        return self.intra_file_hunk_pairs 
        
    def diff_result_to_changed_hunks(self):
        '''
        Analyze diff results, 
        Return:
         * base_changed hunks (line numbers and source) 
         * target_changed hunks
         * diff_reported_mapped_hunk_index, it records which hunk maps contains the interest element
        '''

        should_source_collection_start = False
        change_hunk_index = -1 # starts at 0
        diff_reported_mapped_hunk_index = None
        base_line_number = 0
        target_line_number = 0

        diffs = self.diff_result.split("\n")
        for diff_line in diffs:
            diff_line = diff_line.strip()
            if diff_line.startswith("@@"):
                # eg,. @@ -168,14 +168,13 @@
                # Line numbers starts at 1, step is the absolute numbers of lines.
                if self.base_hunk_range:
                    hunk_pair = HunkPair(self, diff_reported_mapped_hunk_index)
                    self.intra_file_hunk_pairs.append(hunk_pair)
                    self.clear() # Clear the previous hunk info, move to the next

                change_hunk_index +=1
                if change_hunk_index == 0: # Only set it true once
                    should_source_collection_start = True

                tmp = diff_line.split(" ")
                self.base_hunk_range, base_line_number = get_hunk_ranges_from_diff_line(tmp, 1, "-")
                self.target_hunk_range, target_line_number = get_hunk_ranges_from_diff_line(tmp, 2, "+")

                if list(set(self.interest_line_range) & set(self.base_hunk_range)):
                    # Range overlap
                    diff_reported_mapped_hunk_index = change_hunk_index
                    
            if should_source_collection_start == True and not diff_line.startswith("@@"):
                if diff_line.startswith("-"):
                    diff_line = diff_line.replace("-", "", 1)
                    self.base_real_changed_hunk_source.append(diff_line)
                    self.base_real_changed_line_numbers.append(base_line_number)
                    self.base_hunk_source.append(diff_line)
                    base_line_number +=1
                elif diff_line.startswith("+"):
                    diff_line = diff_line.replace("+", "", 1)
                    self.target_real_changed_hunk_source.append(diff_line)
                    self.target_real_changed_line_numbers.append(target_line_number)
                    self.target_hunk_source.append(diff_line)
                    target_line_number +=1
                else:
                    self.base_hunk_source.append(diff_line)
                    self.target_hunk_source.append(diff_line)
                    base_line_number +=1
                    target_line_number +=1

        if self.base_hunk_range:
            hunk_pair = HunkPair(self, diff_reported_mapped_hunk_index)
            self.intra_file_hunk_pairs.append(hunk_pair)
            self.clear()
            
        return self.intra_file_hunk_pairs

    def clear(self):
        self.base_hunk_range = ""
        self.target_hunk_range = ""
        self.base_hunk_source = [] 
        self.target_hunk_source = []
        self.base_real_changed_line_numbers = []
        self.target_real_changed_line_numbers = []
        self.base_real_changed_hunk_source = []
        self.target_real_changed_hunk_source = []