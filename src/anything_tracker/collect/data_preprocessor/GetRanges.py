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
 3. For class, pair the braces. {}
 4. For method, no line numbers in histories. # TODO
'''

import os
from os.path import join
import tempfile
from git.repo import Repo


class GetRanges():
    def __init__(self, repo_dir, commit, file, start_line_number_str, additional_info, repo_url):
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
        self.repo_url =repo_url

        self.four_element_range = None # to return

    def run(self):
        try:
            repo = Repo(self.repo_dir)
            repo.git.checkout(self.commit, force=True)
            self.get_range()
            if self.four_element_range:
                if self.four_element_range.count(0) >= 2:
                    return None
            return self.four_element_range
        except:
            with tempfile.TemporaryDirectory() as demo_path:
                repo_name = self.repo_dir.split("/")[-1]
                temp_repo_dir = join(demo_path, repo_name)
                Repo.clone_from(self.repo_url, temp_repo_dir)
                repo = Repo(temp_repo_dir)
                repo.git.checkout(self.commit, force=True)
                self.file = self.file.replace(self.repo_dir, temp_repo_dir)
                self.get_range()
                if self.four_element_range:
                    if self.four_element_range.count(0) >= 2:
                        return None
                return self.four_element_range

    def get_range(self):
        if not os.path.exists(self.file):
            # introduce a new file, the file does not exist in parent commit.
            return
        
        with open(self.file, "r") as f:
            file_lines = f.readlines()
        
        start_line_number = int(self.start_line_number_str)
        start_line_number_idx = start_line_number - 1
        start_line = file_lines[start_line_number_idx]

        if isinstance(self.additional_info, int): # block
            start_character_abs = len(start_line) - len(start_line.lstrip()) + 1
            end_character_abs = len(file_lines[self.additional_info-1].rstrip)
            self.four_element_range = [start_line_number, start_character_abs, self.additional_info, end_character_abs]
        elif isinstance(self.additional_info, str): # variable, attribute
            intra_line_location_num = start_line.count(self.additional_info)
            if intra_line_location_num > 1:
                print(f"\nintra-line multi-location: {intra_line_location_num}, {self.commit}, {self.file}\n")
            if intra_line_location_num == 0: # newly added
                self.four_element_range = [start_line_number, 0, start_line_number, 0]
            else:
                start_character_abs = start_line.index(self.additional_info) + 1
                end_character_abs = start_character_abs + len(self.additional_info) - 1
                self.four_element_range = [start_line_number, start_character_abs, start_line_number, end_character_abs]
        else: # class, method
            lines_to_check = file_lines[start_line_number_idx:]
            file_lines_max = len(file_lines) + 1
            left_braces_num = 0
            right_brace_num = 0
            end_line_number = None
            end_character_abs = None
            comment_end = True
            for i_abs, line in zip(range(start_line_number, file_lines_max), lines_to_check):
                if comment_end == False:
                    if line.rstrip().endswith("*/"):
                        comment_end = True
                    else:
                        continue

                if not line.lstrip().startswith(("//", "/*", "@")): # exclude comment lines, annotations
                    #TODO { or } may just be a char in a string -> yes, it happens
                    if line.rstrip().endswith("{"):
                    # if "{" in line:
                        left_braces_num += 1
                    if line.rstrip().endswith("}"): # comment follows?
                    # if "}" in line:
                        right_brace_num += 1
                    if left_braces_num != 0 and left_braces_num == right_brace_num:
                        end_line_number = i_abs
                        end_character_abs = len(line)
                        break
                elif line.startswith("/*"):
                    # /* --> multi-line comment
                    # /** --> documentation
                    comment_end = False

            assert end_line_number != None

            start_character_abs = len(start_line) - len(start_line.lstrip()) + 1
            self.four_element_range = [start_line_number, start_character_abs, end_line_number, end_character_abs]
