import subprocess
from git.repo import Repo


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
            elif line.startswith("R") or line.startswith("C"):
                tmp = line.split("\t")
                assert tmp[2] == source_file_path
                renamed_file_path = tmp[1]
                # commit_file_pairs.update({current_commit: renamed_file_path})
                if len(commits) == 1: # the first commit, and it renamed the file
                    file_paths.append(source_file_path)
                else:
                    file_paths.append(renamed_file_path)
                source_file_path = renamed_file_path
    
    if len(commits) != len(file_paths):
        file_paths.append(source_file_path) # for the last commit block
    assert len(commits) == len(file_paths)
    return commits, file_paths # newer to older