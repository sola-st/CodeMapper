import json
from multiprocessing import Pool, cpu_count
import os
from os.path import join
import subprocess
from anything_tracker.collect.data_preprocessor.utils.CommitRangePiece import get_commit_range_pieces
from anything_tracker.collect.suppression.GetSuppressionRange import GetSuppressionRange
from anything_tracker.collect.suppression.SuppressionTypeNumericMaps import read_to_get_type_numeric_maps
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.multiple.GetTargetFilePath import get_target_file_path


def write_extracted_json_strings(json_file, to_write):
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)

def get_json_strs(url, file_path, commit, range, suppression_text, suppression_characters, mapped_oracle_idx):
    converted_json_str_histories = {
        "url": url,
        "file_path": file_path,
        "commit": commit,
        "range": range,
        "source_info_study": suppression_text,
        "source_info_extracted": suppression_characters,
        "mapped_oracle_idx": mapped_oracle_idx
    }
    return converted_json_str_histories

class SuppressionDataConversion():
    def __init__(self, type_numeric_maps, repo_parent_folder, result_parent_folder, file_path, repo_name, url):
        self.type_numeric_maps = type_numeric_maps 
        self.repo_parent_folder = repo_parent_folder
        self.result_parent_folder = result_parent_folder
        self.file_path = file_path
        self.repo_name = repo_name
        self.url = url
        self.repo_dir = join(repo_parent_folder, repo_name)

    def check_if_meaningless_cases(self, history_list):
        # return a value to show keep to extract the range or not
        to_get_range = False

        add_event = history_list[0]
        add_operation = add_event["change_operation"]
        if add_operation == "merge add":
            return to_get_range
        
        end_event = history_list[1] # delete or remaining event

        source_commit = add_event["commit_id"] # older commit
        source_file = add_event["file_path"]
        target_commit = end_event["commit_id"] 
        target_file = end_event["file_path"]

        # to check if a file is deleted or not changed
        target_file_to_check = get_target_file_path(self.repo_dir, source_commit, target_commit, source_file)
        if (not isinstance(target_file_to_check, bool)) and target_file_to_check == target_file: # includes renamed
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            git_command = f"git diff --ignore-space-at-eol --unified=0 {source_commit}:{source_file} {target_commit}:{target_file}"
            for encoding in encodings_to_try:
                try:
                    result = subprocess.run(git_command, cwd=self.repo_dir, shell=True, encoding=encoding,
                            stdout = subprocess.PIPE, universal_newlines=True)
                    diff_result = result.stdout
                    if diff_result:
                        to_get_range = True
                    break
                except UnicodeDecodeError:
                    print(f"Failed to decode using: {encoding}. Subprocess")

        return to_get_range
        
    def convert_histories(self):
        with open(self.file_path, "r") as f:
            data = json.load(f)

        after_filter_idx = 0 # make indices consecutive 
        for meta_idx, history in enumerate(data):
            converted_history = [] # full version
            extracted_commit_range_pieces = {"url":  url} # simplified version
            
            key = f"# S{meta_idx}"
            history_list = history[key] # 0:add, 1:delete or remaining
            
            # check if the file is deletled or not changed. (meaningless to track)
            to_get_range = self.check_if_meaningless_cases(history_list)
            if to_get_range == False:
                continue

            # extract ranges for history peices
            for h in history_list:
                suppression_text = h["warning_type"]
                if suppression_text in ["[]", None, ""]:
                    break
                
                commit = h["commit_id"]
                file_path = h["file_path"]
                suppression_type = suppression_text.split("=")[1]
                line_number = h["line_number"]
                change_operation = h["change_operation"]

                range = None
                suppression_characters = None
                if change_operation == "merge add": # line number is merge unknown
                    pass
                elif "add" in change_operation or change_operation == "remaining": # add, file add
                    range, suppression_characters = GetSuppressionRange(self.type_numeric_maps, self.repo_dir, commit,\
                            join(self.repo_dir, file_path), line_number, suppression_text, suppression_type).run()
                    if range:
                        range = f"{range}"
                    else: # inaccurate history from suppression study
                        print(f"{change_operation}, {key}, {self.repo_name}")
                        break
                # else: # delete, file delete

                history_str = get_json_strs(self.url, file_path, commit, range, suppression_text, suppression_characters, meta_idx) 
                converted_history.append(history_str)
                extracted_pieces = get_commit_range_pieces(commit, file_path, range)
                extracted_commit_range_pieces.update(extracted_pieces)

            if converted_history:
                # meta_idx is the index in oracle and after_filter_idx is the consecutive idx where filtered the meaningless cases.
                current_folder = join(self.result_parent_folder, self.repo_name, str(after_filter_idx))
                os.makedirs(current_folder, exist_ok=True)

                json_file_full = join(current_folder, "expect_full_histories.json")
                write_extracted_json_strings(json_file_full, converted_history)

                json_file_simple = join(current_folder, "expect_simple.json")
                write_extracted_json_strings(json_file_simple, extracted_commit_range_pieces)

                after_filter_idx += 1


def extract_history_wrapper(args):
    repo_name = args[-2]
    print(f"Convert data for {repo_name}.")
    SuppressionDataConversion(*args).convert_histories()
    print(f"Done for {repo_name}.")


if __name__=="__main__":
    repo_parent_folder = join("data", "repos_suppression")
    repo_file = join("data", "python_repos.txt")
    suppression_oracle_folder = join("data", "oracle_suppression")
    result_parent_folder = join("data", "suppression_data")

    # get numeric type mappings
    type_numeric_maps = read_to_get_type_numeric_maps()

    # prepare repositories
    source_repo_init = SourceRepos(repo_file, repo_parent_folder)
    source_repo_init.checkout_latest_commits()

    # get parameters to start convention
    args_for_all_repos = []
    with open(repo_file, "r") as f:
        repo_urls = f.readlines()

    for url in repo_urls:
        url = url.strip()
        repo_name = url.split("/")[-1].replace(".git", "")
        history_file = join(suppression_oracle_folder, repo_name, "histories_suppression_level_all.json")
        args = [type_numeric_maps, repo_parent_folder, result_parent_folder, history_file, repo_name, url]
        args_for_all_repos.append(args)
        
    cores_to_use = cpu_count() - 1 
    with Pool(processes=cores_to_use) as pool:
        pool.map(extract_history_wrapper, args_for_all_repos)