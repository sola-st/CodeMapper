import subprocess


def get_renamed_file_path(repo_dir, base_commit, target_commit, base_file_path):
    get_renamed_files_command = f"git diff --name-status --diff-filter=R {base_commit} {target_commit}"
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

def deduplicate_candidates(candidates, regions):
    deduplicated_candidates = []
    duplicated_indices = []
    for idx, s in enumerate(candidates):
        r = s.candidate_region_character_range.four_element_list
        if r not in regions:
            regions.append(r)
            deduplicated_candidates.append(s)
        else:
            duplicated_indices.append(idx)
    return deduplicated_candidates, regions, duplicated_indices

def get_context_aware_characters(file_lines, character_range, before_lines, after_lines):
    # character_range: start_line, start_character, end_line, end_character (abs numbers)
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

def get_context_aware_unchanged_characters(file_lines, character_range, before_lines, after_lines, changed_line_numbers):
    all_lines = []
    # character_range: start_line, start_character, end_line, end_character (abs numbers)
    max_idx = len(file_lines) + 1
    all_numbers = list(range(1, max_idx))
    unchanged_numbers = list(set(all_numbers) - set(changed_line_numbers))

    start_line_idx = character_range.start_line_idx - 1
    end_line_idx = character_range.end_line_idx - 1
    start_character_idx = character_range.characters_start_idx - 1
    end_characters_idx = character_range.characters_end_idx # range, right open
    region_first_line = file_lines[start_line_idx][start_character_idx:]
    region_last_line = file_lines[end_line_idx][:end_line_idx]
    region_lines = []
    region_lines.append(region_first_line)
    region_lines.extend(file_lines[start_line_idx+1: end_line_idx])
    region_lines.append(region_last_line)

    pre_lines = []
    post_lines = []
    pre_context_line_nums = locate_lines(start_line_idx, before_lines, unchanged_numbers)
    if pre_context_line_nums:
        pre_lines = file_lines[(pre_context_line_nums[0]-1) : pre_context_line_nums[-1]]
    post_context_line_nums = locate_lines(end_line_idx, after_lines, unchanged_numbers, False)
    if post_context_line_nums:
        post_lines = file_lines[(post_context_line_nums[0]-1) : post_context_line_nums[-1]]

    all_lines.extend(pre_lines)
    all_lines.extend(region_lines)
    all_lines.extend(post_lines)
    context_aware_characters = "".join(all_lines)

    # expected_start_idx = 0
    # if pre_context_line_nums:
    #     expected_start_idx = pre_context_line_nums[0] - 1
    # expected_end_idx = all_numbers[-1]
    # if post_context_line_nums:
    #     expected_end_idx = post_context_line_nums[-1]
    # region_lines = file_lines[expected_start_idx: expected_end_idx]
    # context_aware_characters = "".join(region_lines)

    return context_aware_characters

def locate_lines(line_idx, context_num, unchanged_numbers, start=True):
    context_lines = []
    line_abs = line_idx + 1

    if start == True:
        tmp = []
        for num_abs in unchanged_numbers:
            if num_abs < line_abs:
                tmp.append(num_abs)
            else:
                if len(tmp) > context_num:
                    context_lines = tmp[-context_num:]
                return context_lines
    else:
        for num_abs in unchanged_numbers:
            if len(context_lines) == context_num:
                return context_lines
            if num_abs > line_abs:
                context_lines.append(num_abs)
        return context_lines

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