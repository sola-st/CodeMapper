import json
import os
from os.path import join

from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.multiple.CommitsUtils import get_all_commits


def analyze_involved_commits(data, repo_name, repo_parent_folder, all_lines, jgit_num):
    '''
    Analyze how many commits are involved in each piece of data.
    '''

    start_commit = data["startCommitId"][:8]
    final_history = data["expectedChanges"][-1]
    # special case: "parentCommitId": "0", 
    # the end_commits is the first commit.
    end_commit_parent = final_history["parentCommitId"][:8]
    end_commit = final_history["commitId"][:8]
    # end_commit_parent is oldest commit in these 3 commits
    repo_dir = join(repo_parent_folder, repo_name)
    if repo_name not in all_repo_commit_lists.keys():
        commits_list = get_all_commits(repo_dir)
        all_repo_commit_lists.update({repo_name: commits_list})
    else:
        commits_list = all_repo_commit_lists[repo_name]

    is_real_parent = None
    start_idx = commits_list.index(start_commit)
    try:
        end_parent_idx = commits_list.index(end_commit_parent)
    except:
        end_parent_idx = -1
        is_real_parent = "initial_commit"
    end_ix = commits_list.index(end_commit)

    # compute how many commits are there in 
    # [oldest commit (end_parent_commit): newest commit (start_commit)]
    gap_between_olderst_newest_commit = start_idx - end_parent_idx
    assert gap_between_olderst_newest_commit > 0
    commit_num_need_to_track = gap_between_olderst_newest_commit + 1

    ''' 
    check if the parent commit is 
    * the real parent, or
    * the last one which touches the file, or
    * involved in merge branches
    '''
    
    if end_ix - end_parent_idx  == 1:
        # the olderst history is always 'introduce'
        #TODO remove this check, or change to check all the history pieces.
        is_real_parent = "parent_commit"

    # "\t" to avoid commit ids auto changes to numbers in the output csv file.
    meta_half = f"{repo_name}, {start_idx}, {start_commit}\t, {end_parent_idx}, {end_commit_parent}\t" 
    meta = f"{meta_half}, {end_ix}, {end_commit}\t, {commit_num_need_to_track}, {is_real_parent}"
    all_lines.append([meta])
    
    return all_lines, jgit_num

def recursive_get_json_files(data_folder, repo_parent_folder, all_lines, jgit_num, all_repo_commit_lists):
    files = os.listdir(data_folder)
    for file in files:
        file_path = os.path.join(data_folder, file)
        if os.path.isfile(file_path):
            with open(file_path) as f:
              data = json.load(f)

            # repo_name = data["repositoryName"] -- is not always reliable
            repo_name = data["repositoryWebURL"].split("/")[-1].replace(".git", "")
            if repo_name == "jgit":
                # jgit -- remote: Repository not found.
                jgit_num += 1
                print(f"jgit #{jgit_num}: {file_path}")
                continue

            all_lines, jgit_num = analyze_involved_commits(data, repo_name, repo_parent_folder, all_lines, jgit_num)

        elif os.path.isdir(file_path):
            # if file != "test" and file != "training":
            print(file)
            all_lines, jgit_num = recursive_get_json_files(file_path, repo_parent_folder, all_lines, jgit_num, all_repo_commit_lists)

    return all_lines, jgit_num


if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker")
    result_file = join("data", "results", "analysis_on_codetracker_data", "commit_span.csv")

    # prepare repositories
    repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
    repo_folder_java = join("data", "repos_java")
    source_repo_init = SourceRepos(repo_urls_file, repo_folder_java)
    repo_dirs = source_repo_init.get_repo_dirs()
    # source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")
    
    title_half = f"repo name, start commit index, start commit (newest), end commit parent index, end commit parent(oldest)"
    title = f"{title_half}, end commit index, end commit, covered commit number, parent check"
    all_lines = [[title]]

    all_repo_commit_lists = {}
    jgit_num = 0

    all_lines, jgit_num = recursive_get_json_files(data_folder, repo_folder_java, all_lines, jgit_num, all_repo_commit_lists)
    print(f"Number of jgit: {jgit_num}")

    commit_spans = ""
    for line in all_lines:
        line_str = ",".join(line) 
        commit_spans = f"{commit_spans}{line_str}\n"
    with open(result_file, "w") as f:
        f.writelines(commit_spans)