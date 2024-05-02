import subprocess
from git.repo import Repo


def check_modified_commits(repo_dir, start_commit, file_path, category, addtional_info=None):
    '''
    Check only the commit which modify the sepcified file.
    '''

    repo = Repo(repo_dir)
    repo.git.checkout(start_commit, force=True)
    category_tmp = ["attribute", "variable", "block"]
    
    git_command = None
    # if category == "attribute" or category == "variable":
    #     git_command = f"git log -S'{addtional_info}' {file_path}"
    # elif category == "block":
    if category in category_tmp:
        git_command = f"git log -L{addtional_info}:{file_path}"
    else:
        if addtional_info == None: # for initial check
            git_command = f"git log {file_path}" # coarse-grained results, for reference
        else: # is used when tracking the methods and classes.
            git_command = f"git log -L{addtional_info}:{file_path}"

    result = subprocess.run(git_command, cwd=repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
    result_commits = [line.split(" ")[1] for line in result.stdout.split("\n") if line.startswith("commit ")]
    return result_commits

def get_modified_commit_file_pairs(repo_dir, source_commit, source_file_path):
    commits = []
    file_paths = []

    repo = Repo(repo_dir)
    repo.git.checkout(source_commit, force=True)
    
    # focus on checking file renames
    git_command = f"git log --follow --name-status -- {source_file_path}" # --diff-filter=R
    result = subprocess.run(git_command, cwd=repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    result_lines = result.stdout

    if result_lines:
        log_lines = result_lines.strip().split("\n")
        for line in log_lines:
            if line.startswith("commit "):
                if len(commits) != len(file_paths): # no file rename in the previous commit block
                    file_paths.append(source_file_path)
                current_commit = line.replace("commit", "").strip()
                commits.append(current_commit)
                # commit_file_pairs.update({current_commit: source_file_path})
            # R094    src/traverse.py(older commit) src/common/traverse.py(newer commit)
            elif line.startswith("R"):
                tmp = line.split("\t")
                assert tmp[2] == source_file_path
                renamed_file_path = tmp[1]
                # commit_file_pairs.update({current_commit: renamed_file_path})
                file_paths.append(renamed_file_path)
                source_file_path = renamed_file_path
    
    if len(commits) != len(file_paths):
        file_paths.append(source_file_path) # for the last commit block
    assert len(commits) == len(file_paths)
    return commits, file_paths # newer to older