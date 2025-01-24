import json
import os
import random
import re
import subprocess
# from anything_tracker.collect.automated.GetMeaningfulRangesWithAst import GetMeaningfulRangesWithAst
from anything_tracker.collect.automated.GetMeaningfulRangesWithTreeSitter import GetMeaningfulRangesWithTreeSitter
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.utils.RepoUtils import get_x_distance_commits
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


class AutoMarkSourceRegions():
    def __init__(self):
        random.seed(20) # Set the seed for reproducibility
        # customize how many commits/files/source region to select and generate
        self.basic_commit_num = 200 # get latest 200 commit and start random selection
        self.select_commit_num = 10
        self.select_file_num = 3
        self.suffixes = ["py", "java", "js", "cs", "cpp", "go", "ruby", "html"] # "ts", "php",

    def select_random_files(self, repo_dir, base_commit, target_commit):
        selected_files = []
        # get modified files list
        git_command = f"git diff --name-only --diff-filter=M {base_commit} {target_commit}"
        result = subprocess.run(git_command, cwd=repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
        if result.stdout:
            modified_files = [file for file in result.stdout.split("\n") if file.strip().endswith(tuple(self.suffixes))]
            selected_files = modified_files
            if self.select_file_num < len(modified_files):
                selected_files = random.sample(modified_files, self.select_file_num)
        return selected_files

    def run(self):
        '''
        Randomly select meaningful source ranges, for each specified repository:
        * randomly select commits
        * randomly select changed files
        * randomly select start and end lines
        * randomly select start and end indices
        Return a list of generate source region data -> write into a JSON file.
        '''
        random_data = []
        result_folder = join("data", "automated")
        os.makedirs(result_folder, exist_ok=True)
        results_json_file = join(result_folder, "auto_100_tree_sitter.json")

        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs, repo_git_urls = source_repo_init.get_repo_dirs(True)
        source_repo_init.checkout_latest_commits()

        # automatically mark source region start.
        for repo_dir, repo_url in zip(repo_dirs, repo_git_urls):
            repo = Repo(repo_dir)
            print(f"Data generation starts for: {repo_dir}")
            # step 1: randomly select several commits from the latest xx commits.
            selected_commits = select_random_commits(repo, self.basic_commit_num, self.select_commit_num)
            for child_commit in selected_commits:
                distance_commits = get_x_distance_commits(repo_dir, child_commit)
                if not distance_commits:
                    continue
                distance = random.randint(0, len(distance_commits) - 1)
                parent_commit = distance_commits[distance]
                # step 2: randomly select changed files
                selected_files = self.select_random_files(repo_dir, parent_commit, child_commit)
                if not selected_files:
                    continue
                if distance == 0:
                    distance = "neighboring"
                else:
                    distance = f"distance: {distance}"
                # step 3: randomly get source regions
                to_checkout_commit = parent_commit
                target_commit = child_commit
                time_order = "old to new"
                to_checkout = random.randint(0, 1)
                if to_checkout == 1: 
                    to_checkout_commit = child_commit
                    target_commit = parent_commit
                    time_order = "new to old"
                repo.git.checkout(to_checkout_commit, force=True)
                for file in selected_files:
                    selected_file_path = join(repo_dir, file)
                    # print(selected_file_path)
                    hint_changed_line_number_ranges = get_changed_line_hints(repo_dir, parent_commit, child_commit, file)
                    source_range_location, random_mark = GetMeaningfulRangesWithTreeSitter(selected_file_path, hint_changed_line_number_ranges).run()
                    if not random_mark:
                        continue
                    # step 4: form a source region Json string
                    source_dict = {
                        "url" : repo_url.replace(".git", ""),
                        "mapping": {
                            "source_file": file,
                            "target_file": file, # diff -M , so far, no file rename.
                            "source_commit": to_checkout_commit,
                            "target_commit": target_commit,
                            "source_range": f"{source_range_location}",
                            "target_range": None, 
                            "change_operation": "",
                            "kind": distance,
                            "category": random_mark,
                            "time_order": time_order,
                            "detail": ""
                        }
                    }
                    random_data.append(source_dict)

        write_generated_data_to_file(results_json_file, random_data)
    

if __name__=="__main__":
    AutoMarkSourceRegions().run()