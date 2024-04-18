from git.repo import Repo
from os.path import join, exists

def checkout_to_read_file(repo_dir, commit, file_path):
    repo = Repo(repo_dir)
    repo.git.checkout(commit, force=True)
    if exists(join(repo_dir, file_path)):
        with open(join(repo_dir, file_path)) as f:
            file_lines= f.readlines()
        return file_lines
    else:
        return None

def get_region_characters(file_lines, character_range):
    region_characters = []

    # single candidate line
    if character_range.start_line_idx == character_range.end_line_idx:
        region_characters.append(file_lines[character_range.start_line_idx-1][character_range.characters_start_idx-1: character_range.characters_end_idx])
    else:
        # start 
        region_characters.append(file_lines[character_range.start_line_idx-1][character_range.characters_start_idx-1:])

        if character_range.start_line_idx + 1 == character_range.end_line_idx:
            # 2 lines
            region_characters.append(file_lines[character_range.end_line_idx-1][:character_range.characters_end_idx])
        else: # multi-line
            # middle
            region_characters.extend(file_lines[character_range.start_line_idx:character_range.end_line_idx-1])
            # end
            region_characters.append(file_lines[character_range.end_line_idx-1][:character_range.characters_end_idx])
        
    region_characters_str = "".join(region_characters)
    return region_characters_str