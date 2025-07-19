import json
from os.path import join, exists, isdir, dirname
from os import listdir, makedirs
import random
import subprocess
from git.repo import Repo


def get_name_of_main_branch(repo: Repo):
    """
    Returns the name of the main branch of the given repository.
    (Git does not have a concept of a "main branch", so this is a guess
    based on common naming conventions.)
    """
    candidates = [h.name for h in repo.heads]
    if "master" in candidates:
        return "master"
    elif "main" in candidates:
        return "main"
    else:
        return candidates[0]

def get_commit_list(commit_id_csv):
    '''Read given commit .csv file, return a commit list'''
    all_commits = []
    with open(commit_id_csv, "r") as f: # 2 columns: commit and date
        line = f.readline()
        while line:
            tmp =  line.split(",")
            commit = tmp[0].replace("\"", "").strip()
            all_commits.append(commit)
            line = f.readline()
    return all_commits

def write_commit_info_to_csv(repo_dir, commit_id_csv):
    # The newest commits will be the 1st line of the csv file.
    commit_command = "git log --pretty=format:'\"%h\",\"%cd\"' --abbrev=8" # --first-parent" 
    git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    commits = git_get_commits.stdout 

    makedirs(dirname(commit_id_csv), exist_ok=True)
    with open(commit_id_csv, "w") as f:
        f.writelines(commits)

def get_meta_info(change_pair):
    commit = change_pair["commitId"][:8]
    file_path = change_pair["elementFileAfter"]
    tmp = change_pair["elementNameAfter"]
    postfix = tmp.rsplit("#", 1)[1]
    function_name, remaining = postfix.split("(", 1)
    para_declaration_list = remaining.replace(")", "").replace(", ", ",")
    return commit, file_path, function_name, para_declaration_list

def get_variable_location(repo_dir, commit, file_path, function_name, para_declaration_list):
    detailed_location = None
    repo = Repo(repo_dir)
    repo.git.checkout(commit, force=True)
    if join(repo_dir, file_path): 
        subprocess.run(["javac", "-cp", "javaparser-core-3.24.2.jar", "MethodLocator.java"])
        result = subprocess.run([
            "java",
            "-cp", ".:javaparser-core-3.24.2.jar",
            "MethodLocator",
            join(repo_dir, file_path), 
            function_name,
            para_declaration_list,
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result:
            detailed_location = result.stdout.strip()
    return detailed_location
        
def main():
    element = "method" 
    set = "test"
    latest_commit_date = "2025-07-08T00:00:00-00:00"

    repo_folder = join("data", "repos_tracker")
    makedirs(repo_folder, exist_ok=True)

    meta_data = []
    commit_ids = {}

    # download dataset from codetrack github:
    # https://github.com/jodavimehran/code-tracker/tree/master/src/main/resources/oracle
    element_folder = join("oracle", element)
    element_source_files = []
    # element_source_files = ["oracle/method/test/commons-io-CopyUtils-copy.json"]
    # element_source_files = ["oracle/block/test/commons-io-ProxyWriter-write-IF_STATEMENT.json"]
    # element_source_files = ["oracle/block/test/pmd-SourceFileScope-getSubTypes-ENHANCED_FOR_STATEMENT.json"]
    element_source_files = listdir(join(element_folder, set))
    
    for file_idx, file in enumerate(element_source_files):
        # print(join(element_folder, set, file))
        with open(join(element_folder, set, file), "r") as f:
            info = json.load(f) 
        
        git_link = info["repositoryWebURL"]
        # ensure that repos are cloned
        repo_name = git_link.split("/")[-1].replace(".git", "")
        if repo_name == "jgit":
            continue

        change_list:list = info["expectedChanges"]
        change_list.reverse()
        max_change = len(change_list)
        for i, change_pair in enumerate(change_list):
            # older commit related
            target_commit, target_file_path, target_function_name, \
                target_para_declaration_list = get_meta_info(change_pair)
            
            # newer commit related
            source_commit = None
            source_file_path = None
            source_function_name = None
            source_para_declaration_list = None
            if i+1 == max_change:
                source_commit = info["startCommitId"][:8]
                source_file_path = info["filePath"]
                source_function_name = info["functionName"]
                tmp = info["functionKey"].split(f"#{source_function_name}(", 1)[1]
                source_para_declaration_list = tmp.replace(")", "").replace(", ", ",")
            else:
                source_change_pair = change_list[i+1]
                source_commit, source_file_path, source_function_name, \
                    source_para_declaration_list = get_meta_info(source_change_pair)

            # # start parsing
            # git_link = info["repositoryWebURL"]
            # # ensure that repos are cloned
            # repo_name = git_link.split("/")[-1].replace(".git", "")
            # if repo_name == "jgit":
            #     continue

            repo_dir = join(repo_folder, repo_name)
            if not (exists(repo_dir) and isdir(repo_dir)):
                print(f"Cloning {git_link} to {repo_dir}")
                makedirs(repo_dir)
                Repo.clone_from(git_link, repo_dir)

            if repo_name not in commit_ids.keys():
                repo = Repo(repo_dir)
                branch = get_name_of_main_branch(repo)
                latest_commit = next(repo.iter_commits(branch, max_count=1, until=latest_commit_date))
                repo.git.checkout(latest_commit, force=True)
                commit_id = latest_commit.hexsha[:8]
                print(f"Checked out commit {commit_id} of {repo_dir}")

                # get the commit list
                makedirs("sha", exist_ok=True)
                commit_id_csv = join("sha", f"{repo_name}_commits.csv")
                write_commit_info_to_csv(repo_dir, commit_id_csv)
                id_list = get_commit_list(commit_id_csv)
                commit_ids.update({repo_name: id_list}) 

            try: 
                commit_loc_source = commit_ids[repo_name].index(source_commit)
                commit_loc_target = commit_ids[repo_name].index(target_commit)
            except:
                print(f"{file}, source {source_commit}, target {target_commit} not on the main brach.")
                continue

            # target
            target_location = get_variable_location(repo_dir, target_commit, \
                    target_file_path, target_function_name, target_para_declaration_list)
            # source
            source_location = get_variable_location(repo_dir, source_commit, \
                    source_file_path, source_function_name, source_para_declaration_list)
            
            # format codeMapper data
            if source_location and target_location:
                change_operation = "last_pair (unchanged but could differ loc)"
                try:
                    change_operation = source_change_pair["changeType"]
                except:
                    pass
                meta_dict = {
                    "url" : git_link.replace(".git", ""),
                    "mapping": {
                        "source_file": source_file_path,
                        "target_file": target_file_path, 
                        "source_commit": source_commit,
                        "target_commit": target_commit,
                        "source_range": source_location,
                        "target_range": target_location, 
                        "change_operation": change_operation, 
                        "kind": f"distance: {abs(commit_loc_source-commit_loc_target)}",
                        "category": "method",
                        "time_order": "new to old",
                        "detail": ""
                    }
                }
                meta_data.append(meta_dict)
        
        # if (file_idx + 1) % 10 == 0:
        #     print(file_idx)
        #     results_json_file = join("data", "annotation", f"{element}_{set}_{file_idx}.json")
        #     with open(results_json_file, "w") as ds:
        #         json.dump(meta_data, ds, indent=4, ensure_ascii=False)

    random.shuffle(meta_data)
    results_json_file = join("data", "annotation", f"{element}_{set}.json")
    with open(results_json_file, "w") as ds:
        json.dump(meta_data, ds, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()