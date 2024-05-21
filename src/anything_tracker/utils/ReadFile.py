from git.repo import Repo
from os.path import join, exists

def checkout_to_read_file(repo_dir, commit, file_path):
    repo = Repo(repo_dir)
    repo.git.checkout(commit, force=True)
    if exists(join(repo_dir, file_path)):
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings_to_try:
            try:
                with open(join(repo_dir, file_path), "r", encoding=encoding) as f:
                    file_lines = f.readlines()
                break
            except UnicodeDecodeError: # try the next encoding
                print(f"Failed to decode using, {encoding}. {commit}:{file_path}")
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