import json
import random
import subprocess
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.utils.RepoUtils import get_parent_commit
from git.repo import Repo
from os.path import join


random.seed(25) # Set the seed for reproducibility

def select_random_commits(repo, num_commits):
    commit_hashes = [commit.hexsha[:8] for commit in repo.iter_commits(max_count=num_commits)]
    random.shuffle(commit_hashes)
    return commit_hashes

def write_generated_data_to_file(json_file, to_write):
    # random.shuffle(to_write)
    splits_len = len(to_write) // 4
    to_write_1 = to_write[:splits_len]
    to_write_2 = to_write[splits_len:splits_len*2]
    to_write_3 = to_write[splits_len*2:splits_len*3]
    to_write_4 = to_write[splits_len*3:]

    to_write_1.extend(to_write_3)
    to_write_2.extend(to_write_4)

    with open(json_file, "w") as ds:
        json.dump(to_write_1, ds, indent=4, ensure_ascii=False)
    with open(json_file.replace(".json", "_2.json"), "w") as ds:
        json.dump(to_write_2, ds, indent=4, ensure_ascii=False)

def get_data_dict(repo_url, source_file, target_file, source_commit, target_commit, k):
    kind = f"distance: {k}"
    if k == 0:
        kind = "neighboring"

    data_dict = {
        "url" : repo_url,
        "source_file": source_file,
        "target_file": target_file,
        "source_commit": source_commit,
        "target_commit": target_commit,
        "kind": kind,
        "time_order": "old to new"
    }

    is_reversed = random.sample([True, False], 1)[0]
    if is_reversed == True:
        # target region is in the older commit
        data_dict = {
            "url" : repo_url,
            "source_file": target_file,
            "target_file": source_file,
            "source_commit": target_commit,
            "target_commit": source_commit,
            "kind": kind,
            "time_order": "new to old"
        }

    return data_dict


class GetKDistanceCommit():
    def __init__(self, repo_dir, commit, selected_files:list, k_max):
        repo = Repo(repo_dir)
        repo.git.checkout(commit, force=True)
        self.repo_dir = repo_dir
        self.commit = commit
        # 1 neighboring commit (distance 1 commit), and 5 distance-k(k>1) commit, k starts at 1.
        self.selected_files = selected_files
        self.k_max = k_max # including neighboring commit
        
    
    def get_k_distance_commits(self, file):
        '''
        get modified files list

        git log output format: 
            (an example of a piece of commit block, a list of this kind of block are all the output.)
        commit 823cxxx71564xxxxf39cxxxxx872xxx41
        Author: xxxx@xxx.email <xxx@xxx.email>
        Date:   Tue Time xx xx:xx:xx 20xx +0000

            xxxx commit message xxxx
        '''
        git_command = f"git log --max-count={self.k_max} {file}"
        result = subprocess.run(git_command, cwd=self.repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
        related_commits = [line.split(" ")[1][:8] for line in result.stdout.split("\n") if line.startswith("commit ")]
        return related_commits
    
    def select_the_neighboring_distance_commit(self):
        file_for_neighboring_commit = None
        file_for_k_distance_commit = None
        selected_distance_commit = None
        selected_distance_commit_idx = None

        for file in self.selected_files:
            related_commits = self.get_k_distance_commits(file)
            if related_commits:
                related_commits_num = len(related_commits)
                if related_commits_num != 1:
                    # assert related_commits[0] == self.commit # not work for merge commit
                    if related_commits[0] != self.commit:
                        # merge commit
                        # TODO think about how to deal with merge commits
                        continue
                    file_for_neighboring_commit = file
                    related_commits = related_commits[1:]
                    k_recorder = list(range(0, len(related_commits)))
                    selected_distance_commit_idx = random.sample(k_recorder, 1)[0]
                    selected_distance_commit = related_commits[selected_distance_commit_idx]
                    file_for_k_distance_commit = file

                    if file_for_neighboring_commit != None and file_for_k_distance_commit != None:
                        return file_for_neighboring_commit, selected_distance_commit, \
                                selected_distance_commit_idx+2, file_for_k_distance_commit
                    # selected_distance_commit_idx+2. 1 for index starts at 1, 1 for exclude the distance-1(neighboring commit)
        
        # Failed to get k-distance commit on the checkout commit
        return file_for_neighboring_commit, selected_distance_commit, \
                selected_distance_commit_idx, file_for_k_distance_commit 
    
class RandomlyGenerateAnnotationData():
    '''
    Randomly select several files for annotation.
    -- 2 scenarios:
    1) neighboring commit pairs
    2) k-distance commit pairs (the k-commit also touch the selected file)

    For each specified repository:
    * randomly select commits
    * randomly select changed files
    Return a list of annotation-fitted data -> write into a JSON file.
    '''

    def __init__(self):
        # customize how many commits/files to select and generate
        self.basic_commit_num = 100 # get latest 100 commit and start random selection
        self.select_commit_num = 3 # the number of source commit 
        self.select_file_num = 1 
        self.k_max = 5
        self.iteration_num = 2 # get more data to make sure we can annotate meaningful ranges.

    def get_touched_file_list(self, repo_dir, source_commit, target_commit):
        # get modified files list
        git_command = f"git diff --name-only --diff-filter=M {source_commit} {target_commit}"
        result = subprocess.run(git_command, cwd=repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
        modified_files = [file for file in result.stdout.split("\n") if file.strip() != ""]
        return modified_files

    def run(self):
        random_data = []
        results_json_file = join("data", "annotation", "to_annotation.json")

        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs, repo_git_urls = source_repo_init.get_repo_dirs(True)
        source_repo_init.checkout_latest_commits()

        for iter in range(self.iteration_num):
            print(f"Data collection, round #{iter}.")
            random.seed(40)
            for repo_dir, repo_url in zip(repo_dirs, repo_git_urls):
                repo = Repo(repo_dir)
                print(f"Annotation data collection starts for: {repo_dir}")
                # randomly select several commits from the latest 100 commits.
                shuffled_commits = select_random_commits(repo, self.basic_commit_num)
                for commit in shuffled_commits:
                    # shuffled_commits is more than the expected select_commit_num
                    # to make sure we can get enough data (some of the selected commits and files do not have distance_k_commit)
                    neighboring_commit = get_parent_commit(repo_dir, commit) 
                    all_modified_files = self.get_touched_file_list(repo_dir, neighboring_commit, commit)

                    if all_modified_files:
                        random.shuffle(all_modified_files)
                        selected_files = random.sample(all_modified_files, self.select_file_num)
                        init = GetKDistanceCommit(repo_dir, commit, selected_files, self.k_max)
                        info = init.select_the_neighboring_distance_commit() 
                        if None in info:
                            continue
                        else:
                            file_for_neighboring_commit, selected_distance_commit, selected_distance_commit_k, \
                                file_for_k_distance_commit = info

                        # scenario 1
                        neighboring_data_dict = get_data_dict(
                                repo_url, file_for_neighboring_commit, file_for_neighboring_commit, neighboring_commit, commit, 0)
                        if tuple(neighboring_data_dict) not in random_data:
                            random_data.append(neighboring_data_dict)

                        # scenario 2
                        distance_data_dict = get_data_dict(
                                repo_url, file_for_k_distance_commit, file_for_k_distance_commit, \
                                selected_distance_commit, commit, selected_distance_commit_k )
                        if tuple(neighboring_data_dict) not in random_data:
                            random_data.append(distance_data_dict)

                        # *2 is enough, *4 is used to get enough meaningful changes in annotation stage
                        if len(random_data) % (self.select_commit_num * 2) == 0: 
                            break

        write_generated_data_to_file(results_json_file, random_data)
    

if __name__=="__main__":
    RandomlyGenerateAnnotationData().run()