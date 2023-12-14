import json
import random
import subprocess
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.utils.RepoUtils import get_parent_commit
from git.repo import Repo
from os.path import join


random.seed(25)

def select_random_commits(repo, num_commits, select_commit_num):
    commit_hashes = [commit.hexsha[:8] for commit in repo.iter_commits(max_count=num_commits)]
    selected_commits = random.sample(commit_hashes, select_commit_num)
    return selected_commits

def select_random_files(repo_dir, base_commit, target_commit, select_file_num):
    # get modified files list
    git_command = f"git diff --name-only --diff-filter=M {base_commit} {target_commit}"
    result = subprocess.run(git_command, cwd=repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
    modified_files = [file for file in result.stdout.split("\n") if file.strip() != ""]

    selected_files = modified_files
    modified_files_num = len(modified_files)
    if select_file_num <= modified_files_num:
        selected_files = random.sample(modified_files, select_file_num)
    return selected_files

def select_random_source_range(file_contents, max_line_step):
    # step 3.1: randomly get a source region start and end line.
    file_contents_len = len(file_contents)
    start_line_num = random.randint(1, file_contents_len)
    end_line_num = 0 
    max_end = start_line_num + max_line_step
    if max_end + max_line_step + 1 < file_contents_len: # 1 is used to avoid index out of range
        end_line_num = random.randint(start_line_num, max_end)
        
    # step 3.2: randomly get a source region start and end character.
    start_line_len = len(file_contents[start_line_num-1])
    start_character_idx = random.randint(1, start_line_len) # [1, len]

    if end_line_num == 0: # single line source region
        end_character_idx = random.randint(start_character_idx, start_line_len)
        return [start_line_num, start_character_idx, start_line_num, end_character_idx]
    else: # multi-line source region
        end_line_len = len(file_contents[end_line_num-1])
        end_character_idx = random.randint(1, end_line_len)
        return [start_line_num, start_character_idx, end_line_num, end_character_idx]

def write_generated_data_to_file(json_file, to_write):
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)

def main():
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

    # customize how many commits/files/source region to select and generate
    select_commit_num = 3
    select_file_num = 2
    max_line_step = 20

    # prepare repositories
    source_repo_init = SourceRepos()
    repo_dirs, repo_git_urls = source_repo_init.get_repo_dirs(True)
    source_repo_init.checkout_latest_commits()

    # generate data start.
    for repo_dir, repo_url in zip(repo_dirs, repo_git_urls):
        repo = Repo(repo_dir)
        print(f"Data generation starts for: {repo_dir}")
        # step 1: randomly select several commits from the latest 100 commits.
        selected_commits = select_random_commits(repo, 100, select_commit_num)
        for child_commit in selected_commits:
            # assume that parent_commit is base commit, and child_commit is target commit.
            parent_commit = get_parent_commit(repo_dir, child_commit) 
            # step 2: randomly select changed files
            selected_files = select_random_files(repo_dir, parent_commit, child_commit, select_file_num)
            # step 3: randomly get source regions
            repo.git.checkout(parent_commit, force=True)
            for file in selected_files:
                selected_file_path = join(repo_dir, file)
                with open(selected_file_path, "r") as f:
                    file_contents = f.readlines()
                source_range_location = select_random_source_range(file_contents, max_line_step)
                # step 4: form a source region Json string
                url = repo_url + "/commit/" + parent_commit
                # all the Nones are unknown at this point. may will updated by manual check.
                source_dict = {
                    "url" : url,
                    "mapping": {
                        "source_file": file,
                        "target_file": None,
                        "source_range": f"{source_range_location}",
                        "target_range": None,
                        "change_operation": None,
                        "kind": "randomly selected range"
                    }
                }
                random_data.append(source_dict)

    write_generated_data_to_file(results_json_file, random_data)
    

if __name__=="__main__":
    main()