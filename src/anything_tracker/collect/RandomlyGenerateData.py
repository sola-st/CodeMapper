import json
import random
import re
import subprocess
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.utils.RepoUtils import get_parent_commit
from git.repo import Repo
from os.path import join


def select_random_commits(repo, num_commits, select_commit_num):
    commit_hashes = [commit.hexsha[:8] for commit in repo.iter_commits(max_count=num_commits)]
    selected_commits = random.sample(commit_hashes, select_commit_num)
    return selected_commits

def write_generated_data_to_file(json_file, to_write):
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)

def get_changed_line_hints(repo_dir, base_commit, target_commit, file_path):
    hint_changed_line_number_ranges = []

    # make sure some of the randomly generated source regions are involves in changes.
    diff_command = f"git diff --unified=0 {base_commit} {target_commit} -- {file_path}"
    result = subprocess.run(diff_command, cwd=repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
    diff_result = result.stdout.split("\n")
    for diff_line in diff_result:
        if diff_line.strip().startswith("@@"):
            # @@ -168,14 +168,13 @@ | @@ -233 +236 @@ | @@ -235,2 +238 @@
            base_line_relate = diff_line.split(" ")[1] # eg,. -168,14
            # extract all the numbers in input_string
            pattern = r'\b\d+\b'
            numbers = re.findall(pattern, base_line_relate)
            numbers = [int(num) for num in numbers]
            # transfer to real changed number range
            hint_line_range = range(numbers[0], numbers[0]+1)
            num = len(numbers) # can be 1 or 2
            if num == 2 and numbers[1] != 0:
                hint_line_range = range(numbers[0], numbers[0] + numbers[1])
            hint_changed_line_number_ranges.append(hint_line_range)
    return hint_changed_line_number_ranges


class RandomlyGenerateData():
    def __init__(self):
        random.seed(25) # Set the seed for reproducibility
        # customize how many commits/files/source region to select and generate
        self.basic_commit_num = 100 # get latest 100 commit and start random selection
        self.select_commit_num = 3
        self.select_file_num = 2
        self.max_line_step = 20 # source range step
        # to make sure the generated source range have a probability that involves in changed lines
        self.close_to_range_factor = 5 # a factor that close to change hunk line numbers
        self.selection_rate = 0.9 # percentage of selected start line numbers close or is changed line numbers

    def select_random_files(self, repo_dir, base_commit, target_commit):
        # get modified files list
        git_command = f"git diff --name-only --diff-filter=M {base_commit} {target_commit}"
        result = subprocess.run(git_command, cwd=repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
        modified_files = [file for file in result.stdout.split("\n") if file.strip() != ""]

        selected_files = modified_files
        modified_files_num = len(modified_files)
        if self.select_file_num <= modified_files_num:
            selected_files = random.sample(modified_files, self.select_file_num)
        return selected_files

    def select_random_source_range(self, file_contents, hint_ranges):
        # step 3.1: randomly get a source region start and end line.
        kind = None
        # start line
        start_line_num = None
        file_contents_len = len(file_contents)
        if random.random() < self.selection_rate:
            selected_range = random.choice(hint_ranges)
            start_line_num = random.randint(selected_range.start, selected_range.stop)
            kind = "may change"
        else: # get a line closer or is changed line
            start_line_num = random.choice(
                [
                    num for num in range(1, file_contents_len + 1)
                    if all(
                        num < hint_range.start - self.close_to_range_factor or
                        num > hint_range.stop + self.close_to_range_factor
                        for hint_range in hint_ranges
                    )
                ]
            )
            kind = "may no changed"
        # end line
        end_line_num = 0 
        max_end = start_line_num + self.max_line_step
        if max_end + 1 < file_contents_len: # 1 is used to avoid index out of range
            end_line_num = random.randint(start_line_num, max_end)
            
        # step 3.2: randomly get a source region start and end character.
        start_line_len = len(file_contents[start_line_num-1])
        start_character_idx = random.randint(1, start_line_len) # [1, len]

        if end_line_num == 0: # single line source region
            end_character_idx = random.randint(start_character_idx, start_line_len)
            return [start_line_num, start_character_idx, start_line_num, end_character_idx], kind
        else: # multi-line source region
            end_line_len = len(file_contents[end_line_num-1])
            end_character_idx = random.randint(1, end_line_len)
            return [start_line_num, start_character_idx, end_line_num, end_character_idx], kind

    def run(self):
        '''
        Randomly select several source ranges for checking.
        For each specified repository:
        * randomly select commits
        * randomly select changed files
        * randomly select start and end lines
        * randomly select start and end indices
        Return a list of generate source region data -> write into a JSON file.
        '''
        random_data = []
        results_json_file = join("data", "oracle", "change_maps_random.json")

        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs, repo_git_urls = source_repo_init.get_repo_dirs(True)
        source_repo_init.checkout_latest_commits()

        # generate data start.
        for repo_dir, repo_url in zip(repo_dirs, repo_git_urls):
            repo = Repo(repo_dir)
            print(f"Data generation starts for: {repo_dir}")
            # step 1: randomly select several commits from the latest 100 commits.
            selected_commits = select_random_commits(repo, self.basic_commit_num, self.select_commit_num)
            for child_commit in selected_commits:
                # assume that parent_commit is base commit, and child_commit is target commit.
                parent_commit = get_parent_commit(repo_dir, child_commit) 
                # step 2: randomly select changed files
                selected_files = self.select_random_files(repo_dir, parent_commit, child_commit)
                # step 3: randomly get source regions
                repo.git.checkout(parent_commit, force=True)
                for file in selected_files:
                    selected_file_path = join(repo_dir, file)
                    with open(selected_file_path, "r") as f: # base file
                        file_contents = f.readlines()
                    hint_changed_line_number_ranges = get_changed_line_hints(repo_dir, parent_commit, child_commit, file)
                    source_range_location, kind = self.select_random_source_range(file_contents, hint_changed_line_number_ranges)
                    # step 4: form a source region Json string
                    url = repo_url + "/commit/" + child_commit
                    # all the Nones are unknown at this point. may will updated by manual check.
                    source_dict = {
                        "url" : url,
                        "mapping": {
                            "source_file": file,
                            "target_file": None,
                            "source_range": f"{source_range_location}",
                            "target_range": None,
                            "change_operation": None,
                            "kind": kind
                        }
                    }
                    random_data.append(source_dict)

        write_generated_data_to_file(results_json_file, random_data)
    

if __name__=="__main__":
    RandomlyGenerateData().run()