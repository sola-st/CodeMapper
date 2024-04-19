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
from os.path import join, exists
from time import sleep
from git.repo import Repo


def get_range(repo_dir, commit, file, start_line_number_str, additional_info):
    '''
    additional_info has multiple values:
     * None
     * end line number for blocks (int)
     * element for variables and attributes (str)
    '''
    four_element_range = None # to return

    repo = Repo(repo_dir)
    while exists(join(repo_dir, ".git/index.lock")):
        sleep(2)
    repo.git.checkout(commit, force=True)

    if not os.path.exists(file):
        # introduce a new file, the file does not exist in parent commit.
        return four_element_range
    
    with open(file, "r") as f:
        file_lines = f.readlines()
    
    start_line_number = int(start_line_number_str)
    start_line_number_idx = start_line_number - 1
    start_line = file_lines[start_line_number_idx]

    if isinstance(additional_info, int): # block
        start_character_abs = len(start_line) - len(start_line.lstrip()) + 1
        end_character_abs = len(file_lines[additional_info-1].rstrip)
        four_element_range = [start_line_number, start_character_abs, additional_info, end_character_abs]
    elif isinstance(additional_info, str): # variable, attribute
        intra_line_location_num = start_line.count(additional_info)
        if intra_line_location_num > 1:
            print(f"\nintra-line multi-location: {intra_line_location_num}, {commit}, {file}\n")
        if intra_line_location_num == 0: # newly added
            four_element_range = [start_line_number, 0, start_line_number, 0]
        else:
            start_character_abs = start_line.index(additional_info) + 1
            end_character_abs = start_character_abs + len(additional_info) - 1
            four_element_range = [start_line_number, start_character_abs, start_line_number, end_character_abs]
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
        four_element_range = [start_line_number, start_character_abs, end_line_number, end_character_abs]

    return four_element_range # available to return the range characters if needed.
