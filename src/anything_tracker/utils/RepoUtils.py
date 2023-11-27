from os.path import normpath
from os import sep
import git
from git.repo import Repo

def get_name_of_main_branch(repo: Repo):
    """
    Returns the name of the main branch of the given repository.
    (Git does not have a concept of a "main branch", so this is a guess
    based on common naming conventions.)
    """
    candidates = [h.name for h in repo.heads]
    if "master" in candidates:
        return "master"
    elif "main" in candidates:
        return "main"
    else:
        return candidates[0]
    
def repo_dir_to_name(repo_dir):
    return normpath(repo_dir).split(sep)[-1]


def get_parent_commit(repository_path, commit_sha):
    """
    Get the parent commit of a specified commit.

    Args:
        repository_path (str): Path to the Git repository.
        commit_sha (str): SHA of the commit for which to get the parent.

    Returns:
        str: SHA of the parent commit, or None if no parent is found.
    """
    try:
        repo = Repo(repository_path)
        commit = repo.commit(commit_sha)

        # If the commit has parents, return the SHA of the first parent
        if commit.parents:
            return commit.parents[0].hexsha[:8]
        else:
            print(f"Commit {commit_sha} has no parent.")
            return None

    except git.exc.InvalidGitRepositoryError as e:
        print(f"Invalid Git repository at {repository_path}.")
        return None
    except git.exc.GitCommandError as e:
        print(f"Error executing Git command: {e}")
        return None
