import json
import os
from os.path import join


def get_region_base_info(element_name_info):
    tmp = element_name_info.split(".")[-1].split("(")
    info = f"({tmp[0]}"
    line_number = tmp[1].replace(")", "")
    return info, line_number

def convert_change_type():
    '''
    Rules to convert "changeType" (codetracker) to "change_operation" (AnythingTracker).
    * The goal to set these rules is to filter out no change histories.
    * Check if deletions
        1. to nochange
        2. to 

    '''

    change_operation = None
    return change_operation

def write_extracted_json_strings(json_file, to_write):
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)


class DataExtractionAndConversion():
    def __init__(self, data_folder, output_folder):
        self.data_folder = data_folder
        self.output_folder = output_folder

        # change types from the original dataset
        self.change_types_equals_to_nochange = []
        
    def convert_data(self, json_file, category):
        '''
        Convert data to extract what AnythingTracker needs.
        '''

        with open(json_file) as f:
            data = json.load(f)
        
        start_file_path = data["filePath"]
        change_histories = data["expectedChanges"]
        start_line_number = data["attributeDeclarationLine"]
        # 1. input used to start tracking. 
        # Always track back, always end with "introduce" - eg., introduce a new variable.
        converted_json_str_input = { 
            "url": data["repositoryWebURL"],
            "source_file": start_file_path, 
            "source_commit": data["startCommitId"],
            "source_range": f"[{start_line_number}, x, END, y]", 
            "category": category,
            "time_order": "old to new"
        }

        # 2. expected histories
        converted_json_str_expect = self.analyze_histories(change_histories)

        file_for_input = join(self.output_folder, category, "source.json")
        write_extracted_json_strings(file_for_input, converted_json_str_input)
        file_for_expect = join(self.output_folder, category, "expect.json")
        write_extracted_json_strings(file_for_expect, converted_json_str_expect)
            
    def analyze_histories(self, change_histories):
        # Change_histories is a list of json strings, every josn string is a peice of change history
        extracted_change_histories = []

        for h in change_histories:
            if h["changeType"] not in self.change_types_equals_to_nochange:
                change_opreation = convert_change_type()
                source_info, source_line_number = get_region_base_info(h["elementNameBefore"])
                target_info, target_line_number = get_region_base_info(h["elementNameAfter"])
                extracted_h = {
                    "source_commit": h["parentCommitId"],
                    "target_commit": h["commitId"],
                    "source_file": h["elementFileBefore"],
                    "target_file": h["elementFileAfter"],
                    "change_operation": change_opreation,
                    "source_info": source_info,
                    "target_info": target_info,
                    "source_line_number": source_line_number,
                    "target_line_number": target_line_number,
                    "comment": h["comment"]
                }
                extracted_change_histories.append(extracted_h)

        return extracted_change_histories


    def recursive_get_json_files(self, category):
        files = os.listdir(self.data_folder)
        for file in files:
            file_path = os.path.join(self.data_folder, file)
            if os.path.isfile(file_path):
                self.convert_data(file_path, category)
            elif os.path.isdir(file_path):
                if file != "test" and file != "training":
                    category = file
                self.recursive_get_json_files(file_path, category)
