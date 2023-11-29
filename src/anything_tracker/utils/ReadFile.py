from git.repo import Repo
from os.path import join

def checkout_to_read_file(repo_dir, commit, file_path):
    repo = Repo(repo_dir)
    repo.git.checkout(commit, force=True)
    with open(join(repo_dir, file_path)) as f:
        file_lines= f.readlines()
    return file_lines