'''
The original data has 5 categories:
 * attribute
 * class
 * method
 * variable
 * block

Ways to get ranges:
 1. For variable, and attribute, index them in the provided line. [check if multiple locations exist.]
 2. For block, it provides both start and end line number.
 3. For class and method, run AST to get the ranges.
'''

import os
import re
from git.repo import Repo


class GetRanges():
    def __init__(self, repo_dir, commit, file, start_line_number_str, additional_info, suppression=False):
        self.repo_dir = repo_dir
        self.commit = commit
        self.file= file
        self.start_line_number_str = start_line_number_str
        '''
        additional_info has multiple values:
        * None
        * end line number for blocks (int)
        * element for variables and attributes (str)
        '''
        self.additional_info = additional_info
        self.suppression = suppression

        self.four_element_range = None # to return
        self.multi_location_recorder = None

    def run(self):
        repo = Repo(self.repo_dir)
        repo.git.checkout(self.commit, force=True)
        self.get_range()
        return self.four_element_range, self.multi_location_recorder

    def get_range(self):
        if not os.path.exists(self.file):
            # introduce a new file, the file does not exist in parent commit.
            return
        
        with open(self.file, "r") as f:
            file_lines = f.readlines()
        
        start_line_number = int(self.start_line_number_str)
        start_line_number_idx = start_line_number - 1
        try:
            start_line = file_lines[start_line_number_idx]
        except:
            return # newly added
        
        start_character_abs = len(start_line) - len(start_line.lstrip()) + 1 # pre whitespaces
        
        if self.suppression:
            end_character_abs = len(start_line)
            self.four_element_range = [start_line_number, start_character_abs, start_line_number, end_character_abs]

        if isinstance(self.additional_info, int): # block
            end_character_abs = len(file_lines[self.additional_info-1].rstrip())
            self.four_element_range = [start_line_number, start_character_abs, self.additional_info, end_character_abs]
        elif isinstance(self.additional_info, str): # variable, attribute
            end_character_abs = 0
            additonal_check = True
            start_line_splits = start_line.split(" ")
            intra_line_location_num = start_line_splits.count(self.additional_info)
            if intra_line_location_num == 1:
                addi_idx = start_line_splits.index(self.additional_info)
                start_line_splits = start_line_splits[:addi_idx]
                additonal_check = False
            elif intra_line_location_num == 0:
                clean = [re.sub(r"[^\w\s]", "", s).strip() for s in start_line_splits]
                if self.additional_info not in clean:
                    return # newly added
                else:
                    addi_idx = clean.index(self.additional_info)
                    start_line_splits = start_line_splits[:addi_idx]
                    additonal_check = False
            else:
                print(f"{intra_line_location_num}, {self.commit}, {self.file}")
                self.multi_location_recorder = [intra_line_location_num, f"{self.commit}", self.file]
                return

            for s in start_line_splits:
                if additonal_check == True:
                    if s.startswith(self.additional_info):
                        if re.sub(r"[^\w\s]", "", s).strip() == self.additional_info:
                            break
                start_character_abs += (len(s) + 1)
            end_character_abs = start_character_abs + len(self.additional_info) -1
            self.four_element_range = [start_line_number, start_character_abs, start_line_number, end_character_abs]
