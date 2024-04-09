import subprocess
from git.repo import Repo


def get_commits_to_track(repo_dir, source_commit, target_commit):
    # The newest commits will be at the top.
    commit_command = "git log --pretty=format:'%h' --abbrev=8" 
    git_get_commits = subprocess.run(commit_command, cwd=repo_dir, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    commits = git_get_commits.stdout 

    commits_list = commits.split("\n")
    track_start_idx = commits_list.index(source_commit)
    track_end_idx = commits_list.index(target_commit)

    start = track_start_idx
    end = track_end_idx
    is_reversed = False
    if start > end:
        start = track_end_idx
        end = track_start_idx
        is_reversed = True

    commits_to_track = commits_list[start: end+1]
    if is_reversed == True:
        commits_to_track.reverse()

    return commits_to_track


def get_only_changed_commits(repo_dir, source_commit, target_commit, distance, newer_commit, file):
    distance = str(int(distance) + 1)
    repo = Repo(repo_dir)
    repo.git.checkout(newer_commit, force=True)
    git_command = f"git log --max-count={distance} {file}"
    result = subprocess.run(git_command, cwd=repo_dir, shell=True,
        stdout = subprocess.PIPE, universal_newlines=True)
    commits_to_track = [line.split(" ")[1][:8] for line in result.stdout.split("\n") if line.startswith("commit ")]
    if newer_commit == target_commit:
        commits_to_track.reverse()
    if target_commit == commits_to_track[-2]:
        commits_to_track = commits_to_track[:-1]
        commits_to_track.insert(0, source_commit)
    assert commits_to_track[0] == source_commit
    assert commits_to_track[-1] == target_commit

    return commits_to_track
