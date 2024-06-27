import json
import os
from os.path import join
from git.repo import Repo
from anything_tracker.experiments.SourceRepos import SourceRepos


class BlockExtraction():
    def __init__(self, data_folder, output_json_file, repo_parent_folder):
        self.data_folder = data_folder
        self.output_json_file = output_json_file
        self.repo_parent_folder = repo_parent_folder
        self.write_mode = "w"
        self.index = 0

    def extract_blocks(self, json_file):
        '''
        Extract the source lines for all the recorded blocks.
        Can be used to check (i)the if-block type and (ii) the enhanced for loop.
        (i) * if
            * if-else
            * if-else if-else
            * ...
        (ii) check what is enhanced for loop
        Make sure the parser can get the correcct range of desried blocks.
        '''

        with open(json_file) as f:
            data = json.load(f)
        
        # get information from the top part of the json files.
        repo_url = data["repositoryWebURL"]
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_dir = join(self.repo_parent_folder, repo_name)
        file_path = data["filePath"]
        block_start_line = data["blockStartLine"]
        block_end_line = data["blockEndLine"]
        commit = data["startCommitId"]

        repo = Repo(repo_dir)
        repo.git.checkout(commit, force=True)
        full_file_path = join(repo_parent_folder, repo_name, file_path)
        with open(full_file_path) as f:
            code_lines = f.readlines()
        block_lines = code_lines[block_start_line-1: block_end_line]

        block_info = {
            "index": self.index,
            "url": repo_url,
            "commit": commit,
            "file": file_path,
            "start_line": block_start_line,
            "end_line": block_end_line,
            "block_lines": block_lines
        }
        
        self.write_extracted_json_strings(block_info)
        if self.write_mode == "w":
            self.write_mode = "a"
        self.index += 1
    

    def write_extracted_json_strings(self, to_write):
        with open(self.output_json_file, self.write_mode) as ds:
            if self.write_mode == "a":
                ds.write(f",\n")
            json.dump(to_write, ds, indent=4, ensure_ascii=False)
            
    def recursive_get_json_files(self, data_folder):
        files = os.listdir(data_folder)
        i = 0
        for file in files:
            file_path = os.path.join(data_folder, file)
            if os.path.isfile(file_path):
                if not file.startswith("jgit-"):
                    self.extract_blocks(file_path)
                    print(f"#{i} done.")
                    i += 1
            elif os.path.isdir(file_path):
                self.recursive_get_json_files(file_path)
                
    def main(self):
        # prepare repositories
        # repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
        # source_repo_init = SourceRepos(repo_urls_file, repo_parent_folder)
        # repo_dirs = source_repo_init.get_repo_dirs()
        # source_repo_init.checkout_latest_commits()
        # print(f"Found {len(repo_dirs)} repositories.")

        self.recursive_get_json_files(self.data_folder)
        

if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker", "block")
    repo_parent_folder = join("data", "repos_java")
    output_folder = join("data", "converted_data")
    os.makedirs(output_folder, exist_ok=True)
    output_json_file =join(output_folder, "blocks_meta.json")

    BlockExtraction(data_folder, output_json_file, repo_parent_folder).main()