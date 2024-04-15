import json
import os
from os.path import join

from anything_tracker.experiments.SourceRepos import SourceRepos


def get_unique_change_types(data, overall:list, category):
    '''
    Extrack the unique values of changeType. --> to extract the rule to convert.
    '''
    change_types:dict = overall[0]
    change_types_detail:dict = overall[1]
    change_histories = data["expectedChanges"]
    for h in change_histories:
        change_type = h["changeType"]
        # overall counting
        if change_type not in change_types.keys():
            change_types.update({change_type: 1})
        else:
            change_types[change_type] += 1
        change_types["all"] += 1

        # count more details
        if category not in change_types_detail.keys():
            change_types_detail.update({category:{}})
            change_types_detail[category].update({change_type: 1})
        else:
            if change_type not in change_types_detail[category].keys():
                change_types_detail[category].update({change_type: 1})
            else:
                change_types_detail[category][change_type] += 1

    return overall

def recursive_get_json_files(data_folder, repo_parent_folder, overall, category):
    files = os.listdir(data_folder)
    for file in files:
        file_path = os.path.join(data_folder, file)
        if os.path.isfile(file_path):
            with open(file_path) as f:
              data = json.load(f)

            repo_name = data["repositoryWebURL"].split("/")[-1].replace(".git", "")
            if repo_name == "jgit":
                # jgit -- remote: Repository not found.
                continue
            
            assert category != None
            overall = get_unique_change_types(data, overall, category)

        elif os.path.isdir(file_path):
            if file != "test" and file != "training":
                category = file
                print(file)
            overall = recursive_get_json_files(file_path, repo_parent_folder, overall, category)

    return overall


if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker")
    result_file = join("data", "results", "analysis_on_codetracker_data", "change_types_details.json")

    # prepare repositories
    repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
    repo_folder_java = join("data", "repos_java")
    source_repo_init = SourceRepos(repo_urls_file, repo_folder_java)
    repo_dirs = source_repo_init.get_repo_dirs()
    # source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")
    
    change_types_all = {"all": 0}
    change_types_detail = {}
    overall = [change_types_all, change_types_detail]
    category = None
    change_types = recursive_get_json_files(data_folder, repo_folder_java, overall, category)
    with open(result_file, "w") as ds:
        json.dump(change_types, ds, indent=4, ensure_ascii=False)
    