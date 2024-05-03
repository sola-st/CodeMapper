import csv
import json
import os
from os.path import join

from anything_tracker.collect.data_preprocessor.GetRanges import GetRanges
from anything_tracker.collect.data_preprocessor.utils.CommitRangePiece import get_commit_range_pieces
from anything_tracker.experiments.SourceRepos import SourceRepos


def write_extracted_json_strings(json_file, to_write):
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


class SuppressionDataConversion():
    def __init__(self, repo_parent_folder, repo_file, suppression_oracle_folder, result_parent_folder):
        self.repo_parent_folder = repo_parent_folder
        self.repo_file = repo_file
        self.suppression_oracle_folder = suppression_oracle_folder
        self.result_parent_folder = result_parent_folder

    def convert_start(self, suppression_csv, commit, url):
        coverted_sources = []
        with open(suppression_csv) as f:
            reader = csv.reader(f)
            for row in reader:
                file_path, suppression_text, line_number = row
                source_range, multi_location_list = GetRanges(self.repo_dir, commit,\
                        join(self.repo_dir, file_path), line_number, suppression_text, True).run()
                source_range = f"{source_range}"
                converted_str = {
                    "url": url,
                    "source_file": file_path,
                    "source_commit": commit,
                    "source_range": source_range,
                    "source_info": suppression_text
                }
                coverted_sources.append(converted_str)
                #TODO check the mapping between source and histories.
                # json_file = join(current_folder, "source.json")
                # write_extracted_json_strings(json_file, converted_history, "w")

        json_file_simple = join(self.result_parent_folder, "converted_suppression.json")
        write_extracted_json_strings(json_file_simple, coverted_sources)
    
    def convert_histories(self, file_path, repo_name, url):
        repo_result_parent_folder = join(self.result_parent_folder, repo_name)
        with open(file_path, "r") as f:
            data = json.load(f)
        i = 0
        for idx, history in enumerate(data):
            converted_history = [] # full version
            extracted_commit_range_pieces = {"url":  url} # simplified version

            key = f"# S{idx}"
            history_list = history[key] # 0:add, 1:delete(if exists)
            for h in history_list:
                change_operation = h["change_operation"]
                if change_operation == "merge add": # line number is merge unknown
                    print(f"{file_path}, {key}")
                    break # skip the current history as it has no clear line number
                
                commit = h["commit_id"]
                file_path = h["file_path"]
                suppression_text = h["warning_type"]
                line_number = h["line_number"]
                range = None
                if "add" in change_operation: # add, file add
                    range, multi_location_list = GetRanges(self.repo_dir, commit,\
                            join(self.repo_dir, file_path), line_number, suppression_text, True).run()
                    range = f"{range}"
                # else: # delete, file delete

                converted_str = {
                    "url": url,
                    "file_path": file_path,
                    "commit": commit,
                    "range": range,
                    "source_info": suppression_text
                }
                converted_history.append(converted_str)

                extracted_pieces = get_commit_range_pieces(commit, file_path, range)
                extracted_commit_range_pieces.update(extracted_pieces)

            if converted_history:
                current_folder = join(repo_result_parent_folder, str(i))
                os.makedirs(current_folder, exist_ok=True)
                json_file = join(current_folder, "expected_full_histories.json")
                write_extracted_json_strings(json_file, converted_history)

                json_file_simple = join(current_folder, "expected_simple.json")
                write_extracted_json_strings(json_file_simple, extracted_commit_range_pieces)
                i+=1

    def run(self):
        # get repo urls
        with open(self.repo_file, "r") as f:
            repo_urls = f.readlines()

        for url in repo_urls:
            url = url.strip()
            repo_name = url.split("/")[-1].replace(".git", "")
            repo_result_parent_folder = join(suppression_oracle_folder, repo_name)
            os.makedirs(repo_result_parent_folder, exist_ok=True)

            self.repo_dir = join(self.repo_parent_folder, repo_name)
            # start status
            files = os.listdir(repo_result_parent_folder)
            for file in files:
                if file.endswith("suppressions.csv"):
                    commit = file.split("-")[0]
                    suppression_csv = join(repo_result_parent_folder, file)
                    self.convert_start(suppression_csv, commit, url)

            # histories
            file_path = join(repo_result_parent_folder, "histories_suppression_level_all.json")
            self.convert_histories(file_path, repo_name, url)
            break


if __name__=="__main__":
    repo_parent_folder = join("data", "repos_suppression")
    repo_file = join("data", "results", "suppression_data", "python_repos.txt")
    suppression_oracle_folder = join("data", "oracle_suppression")
    result_parent_folder = join("data", "suppression_data")

    # prepare repositories
    source_repo_init = SourceRepos(repo_file, repo_parent_folder)
    # repo_dirs = source_repo_init.get_repo_dirs()
    source_repo_init.checkout_latest_commits()
    # print(f"Found {len(repo_dirs)} repositories.")
    # TODO decide to change the 8-digits commits to full or not
    SuppressionDataConversion(repo_parent_folder, repo_file, suppression_oracle_folder, result_parent_folder).run()