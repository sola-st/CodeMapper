import json
from multiprocessing import Pool
import os
from os.path import join

from anything_tracker.collect.data_preprocessor.ConvertChangeTypes import convert_change_type
from anything_tracker.collect.data_preprocessor.GetRanges import get_range
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
        self.partial_categoris = key_init.partial_categoris
        self.key_set = key_init.key_set

        self.all_args = []
        self.overall_input = []
        
    def convert_data(self, file_number, json_file, category):
        '''
        Convert data to extract what AnythingTracker needs.
        '''

        with open(json_file) as f:
            data = json.load(f)
        
        repo_name = data["repositoryWebURL"].split("/")[-1].replace(".git", "")
        repo_dir = join(self.repo_parent_folder, repo_name)

        # Analyze and write expected histories
        change_histories = data["expectedChanges"]
        converted_json_str_expect, extracted_commit_range_pieces, source_info = \
                self.analyze_histories(repo_dir, change_histories, category)
        
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
        source_commit = data["startCommitId"][:8]
        
        additional_info=None
        
        if category in self.partial_categoris:
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
            "source_info": source_info,
            "category": category,
            "time_order": "new to old (backward)"
        } #TODO remove time_order?

        # Write an individual source file for faster checking.
        file_for_input = join(output_dir, "source.json")
        write_extracted_json_strings(file_for_input, converted_json_str_input, "w")

    def analyze_histories(self, repo_dir, change_histories, category):
        # Change_histories is a list of json strings, every josn string is a peice of change history
        extracted_change_histories = []
        extracted_commit_range_pieces = set()

        for h in change_histories:
            change_opreation = convert_change_type(h["changeType"], category)
            if "noChange" in change_opreation:
                continue
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
            
            # keep the way that codetracker use, source commit is the older commit.
            source_commit = h["parentCommitId"][:8]
            target_commit = h["commitId"][:8]
            source_file = h["elementFileBefore"]
            target_file = h["elementFileAfter"]
            target_range_to_json = f"{target_range}"

            extracted_h_full = {
                "source_commit": source_commit,
                "target_commit": target_commit,
                "source_file": source_file,
                "target_file": target_file,
                "change_operation": change_opreation,
                "source_info": source_info,
                "target_info": target_info,
                "source_range": source_range_to_json,
                "target_range": target_range_to_json,
                "category": category,
                "comment": h["comment"]
            }
            extracted_change_histories.append(extracted_h_full)

            # get a simple version of the expected region locations.
            extracted_pieces_1 = get_commit_range_pieces(source_commit, source_file, source_range_to_json)
            extracted_commit_range_pieces.add(str(extracted_pieces_1))
            extracted_pieces_2 = get_commit_range_pieces(target_commit, target_file, source_range_to_json)
            extracted_commit_range_pieces.add(str(extracted_pieces_2))

        return extracted_change_histories, list(extracted_commit_range_pieces), source_info

    def recursive_get_json_files(self, data_folder, category):
        files = os.listdir(data_folder)
        for i, file in enumerate(files):
            file_path = os.path.join(data_folder, file)
            if os.path.isfile(file_path):
                self.all_args.append([i, file_path, category])
                if i == 2:
                    break
            elif os.path.isdir(file_path):
                if file != "test" and file != "training":
                    category = file
                if file != "training":
                    if category != "method": 
                        print(category)
                        self.recursive_get_json_files(file_path, category)
        return self.all_args

    def main(self):
        args = self.recursive_get_json_files(self.data_folder, "attribute")

        cores_to_use = 14
        with Pool(processes=cores_to_use) as pool:
            pool.map(self.wrapper, args)

        # TODO write an overall input file.
        # # write the overall inputs to a json file.
        # file_for_overall_input = join(self.output_folder, "converted_data.json")
        # write_extracted_json_strings(file_for_overall_input, self.overall_input, "w")

    def wrapper(self, args):
        self.convert_data(*args)
        print(f"{args[2]} #{args[0]}: {args[1]} done.")


if __name__=="__main__":
    data_folder = join("data", "oracle_code_tracker/attribute")
    output_folder = join("data", "converted_data")
    repo_parent_folder = join("data", "repos_java")

    # prepare repositories
    repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
    source_repo_init = SourceRepos(repo_urls_file, repo_parent_folder)
    repo_dirs = source_repo_init.get_repo_dirs()
    source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")
    DataExtractionAndConversion(data_folder, output_folder, repo_parent_folder).main()