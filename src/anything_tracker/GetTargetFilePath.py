import subprocess


def run_command(command, repo_dir):
    result = subprocess.run(command, cwd=repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    return result.stdout

def get_target_file_path(repo_dir, source_commit, target_commit, source_file_path):
    '''
    This function identifies modified files by default. Additionally, here also consider:
        Rename (R): The original file no longer exists at its old location, only at the new one.
    
    If the file is deleted, the target commit has no corresponding character range.
    If the file is renamed, we track it in the new file path.
    No file deletion in our cases, but rename exists.
    '''
    target_file_path = None
    
    # This command is faster by specifying the file path, but can not detact renames.
    get_target_files_command = f"git diff --name-status {source_commit} {target_commit} -- {source_file_path}" 
    # with --name-only will still show the source file name, even for the actually deleted cases
    to_check_item = run_command(get_target_files_command, repo_dir)
    # Examples: M    src/traverse.py src/common/traverse.py
    #           D    src/traverse.py src/common/traverse.py
    if to_check_item:
        tmp = to_check_item.split("\t")
        change_type = tmp[0]

        if change_type != "D":
            target_file_path = tmp[1].strip() 
        else:
            get_renamed_files_command = f"git diff --name-status --diff-filter=R {source_commit} {target_commit}" 
            renames = run_command(get_renamed_files_command, repo_dir)
            if renames:
                to_check_list = renames.strip().split("\n")
                for to_check in to_check_list:
                    # R094    src/traverse.py src/common/traverse.py
                    tmp = to_check.split("\t")
                    if tmp[1] == source_file_path:
                        target_file_path = tmp[2]
                        break

    return target_file_path