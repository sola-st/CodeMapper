import subprocess


def check_modified_commits(repo_dir, file_path, category, addtional_info=None):
    '''
    Check only the commit which modify the sepcified file.
    '''
    git_command = None
    if category == "attribute" or category == "variable":
        git_command = f"git log -S'{addtional_info}' {file_path}"
    elif category == "block":
        git_command = f"git log -L{addtional_info} {file_path}"
    else:
        if addtional_info == None: # for initial check
            git_command = f"git log {file_path}" # coarse-grained results, for reference
        else: # is used when tracking the methods and classes.
            git_command = f"git log -L{addtional_info} {file_path}"

    result = subprocess.run(git_command, cwd=repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
    result_commits = [line.split(" ")[1][:8] for line in result.stdout.split("\n") if line.startswith("commit ")]
    return result_commits

