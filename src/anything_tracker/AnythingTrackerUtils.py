import subprocess


def get_renamed_file_path(repo_dir, base_commit, target_commit, base_file_path):
    get_renamed_files_command = f"git diff --name-status --diff-filter=R {base_commit} {target_commit}" #  -- {base_file_path}
    # get_renamed_files_command = f"git log --name-status --diff-filter=R --follow {base_file_path}" # codetracker: git log --follow
    renamed_result = subprocess.run(get_renamed_files_command, cwd=repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    renamed_files = renamed_result.stdout

    renamed_file_path = None
    if renamed_files:
        rename_cases = renamed_files.strip().split("\n")
        for rename in rename_cases:
            # R094    src/traverse.py src/common/traverse.py
            tmp = rename.split("\t")
            if tmp[1] == base_file_path:
                renamed_file_path = tmp[2]
                break

    return renamed_file_path

def deduplicate_candidates(candidates, regions, reorder=False):
    deduplicated_candidates = []
    for s in candidates:
        r = s.candidate_region_character_range.four_element_list
        marker = s.marker
        if regions == []:
            regions.append(r)
            deduplicated_candidates.append(s)
        else:
            if r not in regions:
                if reorder == True and marker.startswith("<A>"):
                    # keep the one from anythingtracker core idea work, especially for single words.
                    regions.insert(0, r)
                    deduplicated_candidates.insert(0, s)
                else:
                    regions.append(r)
                    deduplicated_candidates.append(s)
    return deduplicated_candidates, regions

def get_context_aware_characters(file_lines, character_range, before_lines, after_lines):
    # character_range: start_line, start_character, end_line, end_character
    max_idx = len(file_lines)
    start_line_idx = character_range.start_line_idx
    end_line_idx = character_range.end_line_idx

    expected_start_idx = start_line_idx - before_lines - 1 # starts at 0
    if expected_start_idx < 0:
        expected_start_idx = 0

    expected_end = end_line_idx + after_lines
    if expected_end > max_idx:
        expected_end = max_idx

    # character_list = file_lines[expected_start_idx: expected_end]
    # characters = "".join(character_list)
    # return characters

    pre_lines_list = file_lines[expected_start_idx: start_line_idx]
    pre_lines_str = "".join(pre_lines_list)
    post_lines_list = file_lines[end_line_idx: expected_end]
    post_lines_str = "".join(post_lines_list)
    return pre_lines_str, post_lines_str


def get_source_and_expected_region_characters(file_lines, character_range):
    '''
    Initially get source_region_characters and expected region characters.
    '''
    characters = []

    # character_range: start_line, start_character, end_line, end_character
    start_line_idx = character_range.start_line_idx
    characters_start_idx = character_range.characters_start_idx
    end_line_idx = character_range.end_line_idx
    characters_end_idx = character_range.characters_end_idx

    start_line = str(file_lines[start_line_idx-1])

    if start_line_idx == end_line_idx: 
        # the source or expected region is inside one line.
        # only records one line number, that is, the start and end are on the same line.
        characters.append(start_line[characters_start_idx-1 : characters_end_idx])
    else:
        # covers multi-line
        # separate to 3 sections: start line, middle lines, and end line.
        # section 1: start line : the entire line is covered
        characters_in_start_line = start_line[characters_start_idx-1:] 
    
        # section 2: middle lines : all covered
        characters_in_middle_lines= []
        if start_line_idx + 1 != end_line_idx:
            characters_in_middle_lines = file_lines[start_line_idx : end_line_idx - 1]

        # section 3: end line : [character index [0: specified_index]]
        end_line = str(file_lines[end_line_idx-1]) 
        characters_in_end_line = end_line[:characters_end_idx]

        characters.append(characters_in_start_line) 
        characters.extend(characters_in_middle_lines) 
        characters.append(characters_in_end_line) 

    return characters