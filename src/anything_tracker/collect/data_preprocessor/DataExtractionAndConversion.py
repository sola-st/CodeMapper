import csv
import json
import os
from os.path import join
import time
import jpype
from git.repo import Repo

from anything_tracker.collect.data_preprocessor.GetRanges import GetRanges
from anything_tracker.collect.data_preprocessor.utils.CategorySpecificUtils import get_region_base_info
from anything_tracker.collect.data_preprocessor.utils.CommitRangePiece import get_commit_range_pieces
from anything_tracker.collect.data_preprocessor.utils.UnifyKeys import UnifyKeys
from anything_tracker.experiments.SourceRepos import SourceRepos


def write_extracted_json_strings(json_file, to_write, write_mode):
    with open(json_file, write_mode) as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


class DataExtractionAndConversion():
    def __init__(self, data_folder, output_folder, repo_parent_folder):
        self.data_folder = data_folder
        self.output_folder = output_folder
        self.repo_parent_folder = repo_parent_folder

        # unify the keys for the start.
        # note: the expectedHistories have the same keys for all the 5 categories.
        key_init = UnifyKeys()
        self.partial_categories = key_init.partial_categories
        self.group_1 = key_init.group_1
        self.group_2 = key_init.group_2
        self.key_set = key_init.key_set

        self.class_ast_init = None
        self.method_ast_init = None

        self.overall_source_json_strs = []
        self.multi_location_infos = [["Folder number", "Multi-location", "Commit", "File path"]]

    def convert_data(self, file_number, json_file, category, subfolder):
        '''
        Convert data to extract what AnythingTracker needs.
        '''

        with open(json_file) as f:
            data = json.load(f)
        
        repo_name = data["repositoryWebURL"].split("/")[-1].replace(".git", "")
        repo_dir = join(self.repo_parent_folder, repo_name)

        # Analyze and write expected histories
        change_histories = data["expectedChanges"]
        repo_url = data["repositoryWebURL"]
        converted_json_str_expect, extracted_commit_range_pieces, source_info = \
                self.analyze_histories(repo_dir, change_histories, category, repo_url, file_number)

        if subfolder: 
            output_dir = join(self.output_folder, category, subfolder, str(file_number))
        else:
            output_dir = join(self.output_folder, category, str(file_number))
        os.makedirs(output_dir, exist_ok=True)

        file_for_expect = join(output_dir, "expect_full_histories.json")
        write_extracted_json_strings(file_for_expect, converted_json_str_expect, "w")
        file2_for_expect = join(output_dir, "expect_simple.json")
        write_extracted_json_strings(file2_for_expect, extracted_commit_range_pieces, "w")

        # Write input used to start tracking. 
        # Always track back, always end with "introduce" - eg., introduce a new variable.
        start_file_path = data["filePath"]
        start_line_number = data[self.key_set[category]["start_line_number"]]
        source_commit = data["startCommitId"]
        
        additional_info=None
        if category in self.partial_categories:
            additional_info = data[self.key_set[category]["start_name"]]
        elif category == "block":
            additional_info = data["blockEndLine"]
            
        file_path = join(repo_dir, start_file_path)

        if category in self.group_1:
            source_range, multi_location_list = GetRanges(repo_dir, source_commit, file_path, start_line_number, additional_info).run()
            if multi_location_list:
                multi_location_list.insert(0, file_number)
                self.multi_location_infos.append(multi_location_list)
        else: # group_2
            repo = Repo(repo_dir)
            repo.git.checkout(source_commit, force=True)
            start_name = data[self.key_set[category]["start_name"]]
            element_key_line = data[self.key_set[category]["start_info"]]
            source_info = get_region_base_info(element_key_line, category)
            start_name_copy, identifier = source_info
            assert start_name == start_name_copy
            ast_init = self.class_ast_init
            if category == "method":
                ast_init = self.method_ast_init
            source_range = ast_init.parseJavaFile(file_path, start_name, identifier) 

        converted_json_str_input = { 
            "url":  repo_url,
            "source_file": start_file_path, 
            "source_commit": source_commit,
            "source_range": f"{source_range}", 
            "source_info": source_info,
            "category": category
        }

        # Write an individual source file for faster checking.
        file_for_input = join(output_dir, "source.json")
        write_extracted_json_strings(file_for_input, converted_json_str_input, "w")

        return converted_json_str_input

    def analyze_histories(self, repo_dir, change_histories, category, repo_url, file_number):
        # Change_histories is a list of json strings, every json string is a piece of change history
        extracted_change_histories = []
        extracted_commit_range_pieces = {"url":  repo_url}

        for h in change_histories:
            source_line_number = None
            target_line_number = None
            source_additional_info = None
            target_additional_info = None
            target_range = None # target(newer commit) should always exists

            # the keys for histories are the same for all the 5 categories.
            source_results = get_region_base_info(h["elementNameBefore"], category)
            target_results = get_region_base_info(h["elementNameAfter"], category)

            if category in self.partial_categories:
                # _info shows the source element, like method definition
                source_additional_info, source_line_number = source_results
                target_additional_info, target_line_number = target_results
                source_info = source_additional_info
                target_info = target_additional_info
            elif category == "block":
                source_info, source_line_number, source_end_line_number = source_results
                target_info, target_line_number, target_end_line_number = target_results
                source_additional_info = source_end_line_number
                target_additional_info = target_end_line_number
            else: # method, class
                # _info for reference, it includes:
                #   method/class name, accessors, parameters, line numbers(only for class)
                source_info = source_results
                target_info = target_results
                source_range, target_range = self.analyze_histories_group_2(repo_dir, \
                        h, source_info, target_info, category)
            
            if category not in self.group_2:
                # attribute, variable and block
                source_range, target_range = self.analyze_histories_group_1(repo_dir, \
                        h, source_line_number, target_line_number, \
                        source_additional_info, target_additional_info, file_number)

            if source_range != None: # to handle 'introduce'
                source_range_to_json = f"{source_range}"
            else:
                source_range_to_json = source_range

            # keep the way that codetracker use, source commit is the older commit.
            source_commit = h["parentCommitId"]
            target_commit = h["commitId"]
            source_file = h["elementFileBefore"]
            target_file = h["elementFileAfter"]
            target_range_to_json = f"{target_range}"

            extracted_h_full = {
                "url":  repo_url,
                "source_commit": source_commit,
                "target_commit": target_commit,
                "source_file": source_file,
                "target_file": target_file,
                "change_operation": h["changeType"],
                "source_info": source_info,
                "target_info": target_info,
                "source_range": source_range_to_json,
                "target_range": target_range_to_json,
                "category": category
            }
            try:
                extracted_h_full.update({"comment": h["comment"]})
            except:
                extracted_h_full.update({"comment": ""})
            extracted_change_histories.append(extracted_h_full)

            # get a simple version of the expected region locations.
            extracted_pieces_1 = get_commit_range_pieces(source_commit, source_file, source_range_to_json)
            extracted_commit_range_pieces.update(extracted_pieces_1)
            extracted_pieces_2 = get_commit_range_pieces(target_commit, target_file, target_range_to_json)
            extracted_commit_range_pieces.update(extracted_pieces_2)
        
        return extracted_change_histories, extracted_commit_range_pieces, source_info
    
    def analyze_histories_group_1(self, repo_dir, h, source_line_number, target_line_number, \
            source_additional_info, target_additional_info, file_number):
        # group 1: attribute, variable and block
        assert source_line_number != None
        assert target_line_number != None

        # get range for attribute, variable and block
        source_range = None
        parent_commit = h["parentCommitId"]
        if parent_commit != "0" and h["changeType"] != "introduced":
            source_file_path = join(repo_dir, h["elementFileBefore"])
            source_range, source_multi_location_list = GetRanges(repo_dir, \
                    parent_commit, source_file_path, source_line_number, source_additional_info).run()
            if source_multi_location_list:
                source_multi_location_list.insert(0, file_number)
                self.multi_location_infos.append(source_multi_location_list)
        target_file_path = join(repo_dir, h["elementFileAfter"])  
        target_range, target_multi_location_list = GetRanges(repo_dir, \
                    h["commitId"], target_file_path, target_line_number, target_additional_info).run()
        if target_multi_location_list:
            target_multi_location_list.insert(0, file_number)
            self.multi_location_infos.append(target_multi_location_list)

        return source_range , target_range
    
    def analyze_histories_group_2(self, repo_dir, h, source_reference, target_reference, category):
        # group 2: method and class
        repo = Repo(repo_dir)

        '''
        the parameters to start AST are:
            file_path,
            class name, or method name,                 --> generalized as element_name in current function
            class accessor, or method parameter types.  --> generalized as identifier in current function
        '''

        source_element_name, source_identifier = source_reference
        target_element_name, target_identifier = target_reference

        ast_init = self.class_ast_init
        if category == "method":
            ast_init = self.method_ast_init

        source_range = None
        parent_commit = h["parentCommitId"]
        if parent_commit != "0":
            repo.git.checkout(parent_commit, force=True)
            source_file_path = join(repo_dir, h["elementFileBefore"])
            if os.path.exists(source_file_path):
                source_range = ast_init.parseJavaFile(source_file_path, source_element_name, source_identifier)
            
        repo.git.checkout(h["commitId"], force=True)
        target_file_path = join(repo_dir, h["elementFileAfter"])  
        target_range = ast_init.parseJavaFile(target_file_path, target_element_name, target_identifier)

        return source_range , target_range

    def recursive_get_json_files(self, data_folder, category, subfolder):
        if (category == "method" and not self.method_ast_init) or (category == "class" and not self.class_ast_init) :
            jar_path = "/home/huimin/projects/anything_tracker_related/AnythingTracker/jparser.jar"
            jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % jar_path)
            if category == "method":
                parser_obj = jpype.JClass("jparser.JavaMethodParser")
                self.method_ast_init = parser_obj()
            else:
                parser_obj = jpype.JClass("jparser.JavaClassParser")
                self.class_ast_init = parser_obj()

        files = os.listdir(data_folder)
        i = 0
        for file in files:
            file_path = os.path.join(data_folder, file)
            if os.path.isfile(file_path):
                if not file.startswith("jgit-"):
                    source_json_str = self.convert_data(i, file_path, category, subfolder)
                    print(f"{category}-{subfolder} #{i}: {file_path} done.")
                    self.overall_source_json_strs.append(source_json_str)
                    i += 1
            elif os.path.isdir(file_path):
                if file != "test" and file != "training":
                    category = file
                else:
                    subfolder = file

                if category and subfolder:
                    self.recursive_get_json_files(file_path, category, subfolder)
                    end_time = time.time()
                    print(f"{category}-{subfolder}: {round((end_time - self.start_time), 3)} seconds.\n")

                    # Write an overall source file to start checking.
                    if self.overall_source_json_strs:
                        file_for_overall = join(self.output_folder, f"converted_data_{category}_{subfolder}.json")
                        write_extracted_json_strings(file_for_overall, self.overall_source_json_strs, "w")
                        self.overall_source_json_strs = []

                    if len(self.multi_location_infos) > 1:
                        file_for_multi_location = join(self.output_folder, f"converted_data_{category}_{subfolder}_multi.csv")
                        with open(file_for_multi_location, 'w') as f:
                            writer = csv.writer(f)
                            writer.writerows(self.multi_location_infos)
                        self.multi_location_infos = [["Folder number", "Multi-location", "Commit", "File path"]]
                

    def main(self):
        self.start_time = time.time()
        self.recursive_get_json_files(self.data_folder, None, None)


if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker")
    output_folder = join("data", "converted_data")
    repo_parent_folder = join("data", "repos_java")

    # prepare repositories
    repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
    source_repo_init = SourceRepos(repo_urls_file, repo_parent_folder)
    repo_dirs = source_repo_init.get_repo_dirs()
    source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")
    DataExtractionAndConversion(data_folder, output_folder, repo_parent_folder).main()