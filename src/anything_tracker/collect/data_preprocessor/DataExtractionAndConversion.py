import json
import os
from os.path import join

from anything_tracker.collect.data_preprocessor.GetRanges import get_range
from anything_tracker.experiments.SourceRepos import SourceRepos


def get_region_base_info(element_name_info, category):
    '''
    Format:
        block: src/main/java/org.apache.commons.io.EndianUtils#read(InputStream)$if(475-477)"
        class: src/main/java/org.apache.commons.io.(public)CopyUtils(30)
        variable: src/main/java/com.puppycrawl.tools.checkstyle.Checker#fireErrors(String, SortedSet)$element:LocalizedMessage(387)
        attribute: src/java/org.apache.commons.io.input.Tailer@(final)(private)end:boolean(70)
                java/compiler/impl/src/com.intellij.packaging.impl.artifacts.ArtifactBySourceFileFinderImpl@myProject:Project(47)
    '''

    # only "variable" and "attribute" need perfact 'element'.
    element = None
    if category == "block":
        element = element_name_info.split("#")[-1] # coarse grained result
    elif category == "class":
        element = element_name_info.split(".")[-1]
    elif category == "variable":
        element = element_name_info.split("$element:")[1].split("(")[0]
    elif category == "attribute":
        splits_tmp = element_name_info.split(":")[0]
        if ")" in splits_tmp:
            element = splits_tmp.split(")")[1]
        else:
            element = splits_tmp.split("@")[1]
    # else: # method
    assert element != None

    tmp = element_name_info.split(".")[-1].split("(")
    line_number = tmp[-1].replace(")", "")
    if "-" in line_number: # special for 'block'
        start_line_number, end_line_number = line_number.split("-")
        return element, start_line_number, end_line_number
    else:
        return element, line_number


def write_extracted_json_strings(json_file, to_write, write_mode):
    with open(json_file, write_mode) as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


class DataExtractionAndConversion():
    def __init__(self, data_folder, output_folder, repo_parent_folder):
        self.data_folder = data_folder
        self.output_folder = output_folder
        self.repo_parent_folder = repo_parent_folder
        self.partial_categoris = ["attribute", "variable"]
        self.partial_categoris_3 = ["attribute", "variable"]

        # unify the keys for the start.
        # note: the expectedHistories have the smae keys for all the 5 categories.
        self.key_set = {
            "attribute": {
                "to_split": "attributeKey",
                "start_line_number": "attributeDeclarationLine"
            },
            "class": {
                # "to_split": "classKey",
                "start_line_number": "classDeclarationLine"
            },
            # "method" : {
            #     "to_split": "functionKey",
            #     "start_line_number": "functionStartLine"
            # },
            "variable": {
                "to_split": "variableKey",
                "start_line_number": "variableStartLine"
            },
            "block" : {
                "to_split": "blockKey",
                "start_line_number": "blockStartLine",
                "end_line_number": "blockEndLine"
            }
        }

        # change types from the original dataset
        # self.change_types_equals_to_nochange = []
        
    def convert_data(self, file_number, json_file, category):
        '''
        Convert data to extract what AnythingTracker needs.
        '''

        with open(json_file) as f:
            data = json.load(f)
        
        start_file_path = data["filePath"]
        change_histories = data["expectedChanges"]
        start_line_number = data[self.key_set[category]["start_line_number"]]
        # 1. input used to start tracking. 
        # Always track back, always end with "introduce" - eg., introduce a new variable.
        source_commit = data["startCommitId"][:8]
        repo_name = data["repositoryWebURL"].split("/")[-1].replace(".git", "")
        repo_dir = join(self.repo_parent_folder, repo_name)
        additional_info=None
        
        if category in self.partial_categoris:
            # key = f"{category}Key"
            key = self.key_set[category]["to_split"]
            additional_info, source_line_number = get_region_base_info(data[key], category)
        elif category == "block":
            additional_info = data["blockEndLine"]
        file_path = join(repo_dir, start_file_path)
        source_range = get_range(repo_dir, source_commit, file_path, start_line_number, additional_info)
        converted_json_str_input = { 
            "url": data["repositoryWebURL"],
            "source_file": start_file_path, 
            "source_commit": source_commit,
            "source_range": f"{source_range}", 
            "category": category,
            "time_order": "old to new"
        }

        output_dir = join(self.output_folder, category, str(file_number))
        os.makedirs(output_dir, exist_ok=True)

        file_for_input = join(output_dir, "source.json")
        write_extracted_json_strings(file_for_input, converted_json_str_input, "w")

        # 2. expected histories
        converted_json_str_expect = self.analyze_histories(repo_dir, change_histories, category)
        
        # TODO add to write an overall file
        file_for_expect = join(output_dir, "expect.json")
        write_extracted_json_strings(file_for_expect, converted_json_str_expect, "w")
            
    def analyze_histories(self, repo_dir, change_histories, category):
        # Change_histories is a list of json strings, every josn string is a peice of change history
        extracted_change_histories = []

        for h in change_histories:
            # if h["changeType"] not in self.change_types_equals_to_nochange: #TODO
                # change_opreation = convert_change_type()
                source_line_number = None
                target_line_number = None
                source_additional_info = None
                target_additional_info = None
                if category in self.partial_categoris:
                    # _info shows the source element, like method definition
                    source_additional_info, source_line_number = get_region_base_info(h["elementNameBefore"], category)
                    target_additional_info, target_line_number = get_region_base_info(h["elementNameAfter"], category)
                    source_info = source_additional_info
                    target_info = target_additional_info
                elif category == "block":
                    source_info, source_line_number, source_end_line_number = get_region_base_info(h["elementNameBefore"], category)
                    target_info, target_line_number, target_end_line_number = get_region_base_info(h["elementNameAfter"], category)
                    source_additional_info = source_end_line_number
                    target_additional_info = target_end_line_number
                elif category == "class":
                    source_info, source_line_number = get_region_base_info(h["elementNameBefore"], category)
                    target_info, target_line_number = get_region_base_info(h["elementNameAfter"], category)

                assert source_line_number != None
                assert target_line_number != None

                source_range = None
                parent_commit = h["parentCommitId"][:8]
                if parent_commit != "0":
                    source_file_path = join(repo_dir, h["elementFileBefore"])
                    source_range = get_range(repo_dir, parent_commit, source_file_path, source_line_number, source_additional_info)
                target_file_path = join(repo_dir, h["elementFileAfter"])  
                target_range = get_range(repo_dir, h["commitId"][:8], target_file_path, target_line_number, target_additional_info)

                if source_range != None: # to handle 'introduce'
                    source_range_to_json = f"{source_range}"
                else:
                    source_range_to_json = source_range
                    
                extracted_h = {
                    "source_commit": h["parentCommitId"],
                    "target_commit": h["commitId"],
                    "source_file": h["elementFileBefore"],
                    "target_file": h["elementFileAfter"],
                    "change_operation": h["changeType"],
                    "source_info": source_info,
                    "target_info": target_info,
                    "source_range": source_range_to_json,
                    "target_range": f"{target_range}",
                    "category": category,
                    "comment": h["comment"]
                }
                extracted_change_histories.append(extracted_h)

        return extracted_change_histories

    def recursive_get_json_files(self, data_folder, category):
        files = os.listdir(data_folder)
        for i, file in enumerate(files):
            file_path = os.path.join(data_folder, file)
            if os.path.isfile(file_path):
                self.convert_data(i, file_path, category)
            elif os.path.isdir(file_path):
                if file != "test" and file != "training":
                    category = file
                if category != "method" and category != "training":
                    print(category)
                    self.recursive_get_json_files(file_path, category)


if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker/attribute")
    output_folder = join("data", "converted_data")
    repo_parent_folder = join("data", "repos_java")

    # prepare repositories
    repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
    source_repo_init = SourceRepos(repo_urls_file, repo_parent_folder)
    repo_dirs = source_repo_init.get_repo_dirs()
    # source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")
    DataExtractionAndConversion(data_folder, output_folder, repo_parent_folder).recursive_get_json_files(data_folder, "attribute")