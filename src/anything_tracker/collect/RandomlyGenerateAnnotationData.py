import json
import random
import subprocess
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.utils.RepoUtils import get_parent_commit
from git.repo import Repo
from os.path import join

seed_num = 25
random.seed(seed_num) # Set the seed for reproducibility

def select_random_commits(repo, num_commits):
    commit_hashes = [commit.hexsha[:8] for commit in repo.iter_commits(max_count=num_commits)]
    random.shuffle(commit_hashes)
    return commit_hashes

def write_generated_data_to_file(json_file, to_write, iteration_num):
    splits_len = len(to_write) // iteration_num
    # write into 2 files
    to_write_1 = []
    to_write_2 = []

    start = 0
    end = splits_len
    for i in range(iteration_num):
        if i % 2 != 0:
            to_write_1.extend(to_write[start:end])
        else:
            to_write_2.extend(to_write[start:end])
        start = end
        end += splits_len
        if i + 1 == iteration_num:
            end = len(to_write) # take all the remianing data

    with open(json_file, "w") as ds:
        json.dump(to_write_1, ds, indent=4, ensure_ascii=False)
    with open(json_file.replace("_1.json", "_2.json"), "w") as ds:
        json.dump(to_write_2, ds, indent=4, ensure_ascii=False)

def get_data_dict(repo_url, source_file, target_file, source_commit, target_commit, k):
    kind = f"distance: {k}"
    if k == 1:
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
        '''
        Return base_file, selected_file, selected_commit, idx for selected_commit.

        if no file rename cases: base_file == selected_file
        if file rename happens, the logic should be changed
        '''
        for file in self.selected_files:
            related_commits = self.get_k_distance_commits(file)
            if related_commits:
                is_distance = random.sample([True, False], 1)[0] # False: neighboring or True: k>1 distance
                if len(related_commits) == 1:
                    if is_distance == True:
                        # always be the current commit, or neighboring commit
                        # no distance commit
                        return None, None, None, None
                    else: # get a neighboring case
                        if related_commits[0] != self.commit:
                            # return a neiboring commit mapping
                            return file, file, related_commits[0], 1
                        else:
                            # only current commit changes the file, failed to get a neighboring/distance commit
                            return None, None, None, None 
                        
                # len(related_commits) > 1
                idx_delta = 1 # 1 for letting index starts at 1
                if related_commits[0] == self.commit:
                    related_commits = related_commits[1:] # exclude current commit
                
                if is_distance == True:
                    related_commits = related_commits[1:] 
                    idx_delta += 1 # exclude neighboring commit

                if related_commits:
                    k_recorder = list(range(0, len(related_commits)))
                    selected_distance_commit_idx = random.sample(k_recorder, 1)[0]
                    selected_distance_commit = related_commits[selected_distance_commit_idx]
                    return file, file, selected_distance_commit, selected_distance_commit_idx + idx_delta
                else:
                    return None, None, None, None 
        
        # Failed to get k-distance commit on the checkout commit, return Nones
        return None, None, None, None 
    
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
        self.basic_commit_num = 200 # get latest x commit and start random selection
        self.select_commit_num = 6 # the number of source commit 
        self.select_file_num = 1 
        self.k_max = 5
        self.iteration_num = 4 # get more data to make sure we can annotate meaningful ranges.

    def get_touched_file_list(self, repo_dir, source_commit, target_commit):
        # get modified files list
        git_command = f"git diff --name-only --diff-filter=M {source_commit} {target_commit}"
        result = subprocess.run(git_command, cwd=repo_dir, shell=True,
            stdout = subprocess.PIPE, universal_newlines=True)
        modified_files = [file for file in result.stdout.split("\n") if file.strip() != ""]
        return modified_files

    def run(self):
        random_data = [] # the elements is round data
        results_json_file = join("data", "annotation", "updated_to_annotation_deduplicated_1.json")

        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs, repo_git_urls = source_repo_init.get_repo_dirs(True)
        source_repo_init.checkout_latest_commits()

        to_control_ratio = int(self.select_commit_num / 2) # ratio between neighboring and 
        for iter in range(self.iteration_num):
            round_data = [] # collect all the dicts in current round
            random.seed(seed_num + iter*iter) # change a seed for every iteration
            for repo_dir, repo_url in zip(repo_dirs, repo_git_urls):
                repo = Repo(repo_dir)
                print(f"Round #{iter}. starts for: {repo_dir}")
                repo_level_neighboring = []
                repo_level_distance = []
                # randomly select several commits from the latest 100 commits.
                shuffled_commits = select_random_commits(repo, self.basic_commit_num)
                for commit in shuffled_commits:
                    # shuffled_commits is more than the expected select_commit_num
                    # to make sure we can get enough data (some of the selected commits and files do not have distance_k_commit)
                    parent_commit = get_parent_commit(repo_dir, commit) 
                    all_modified_files = self.get_touched_file_list(repo_dir, parent_commit, commit)

                    if all_modified_files:
                        # random.shuffle(all_modified_files)
                        selected_files = random.sample(all_modified_files, self.select_file_num) # list
                        init = GetKDistanceCommit(repo_dir, commit, selected_files, self.k_max)
                        info = init.select_the_neighboring_distance_commit() 
                        if None in info:
                            continue
                        else:
                            # file_for_neighboring_commit is not used, beacause here is no file rename cases.
                            file_in_current_commit, file_in_seleted_commit, selected_commit, distance_k = info

                        distance_data_dict = get_data_dict(
                                repo_url, file_in_current_commit, file_in_seleted_commit, selected_commit, commit, distance_k)
                        
                        if distance_k > 1: # distance_k can be 1 - 5
                            if tuple(distance_data_dict) not in repo_level_distance:
                                repo_level_distance.append(distance_data_dict)
                        else:
                            if tuple(distance_data_dict) not in repo_level_neighboring:
                                repo_level_neighboring.append(distance_data_dict)

                        neigh_len = len(repo_level_neighboring)
                        dist_len = len(repo_level_distance)
                        if neigh_len >= to_control_ratio and dist_len >= to_control_ratio:
                            round_data.extend(repo_level_neighboring[:to_control_ratio])
                            round_data.extend(repo_level_distance[:to_control_ratio])
                            break
            # 1 round ends
            random.shuffle(round_data)
            if random_data == []:
                random_data.extend(round_data)
            else: # deduplicate the different rounds
                for t in round_data:
                    if t not in random_data:
                        random_data.append(t)

        write_generated_data_to_file(results_json_file, random_data, self.iteration_num)
    

if __name__=="__main__":
    RandomlyGenerateAnnotationData().run()