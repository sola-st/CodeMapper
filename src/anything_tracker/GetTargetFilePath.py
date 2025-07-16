import subprocess
from git import Repo
import re
from datetime import datetime


def run_command(command, repo_dir):
    result = subprocess.run(command, cwd=repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    return result.stdout

def get_target_file_path(repo_dir, source_commit, target_commit, source_file_path):
    target_file_path = None
    # checkout to the newer commit
    repo = Repo(repo_dir)
    source = repo.commit(source_commit)
    target = repo.commit(target_commit)

    newer_commit = source_commit
    if source.committed_date < target.committed_date:
        newer_commit = target_commit
    repo.git.checkout(newer_commit, force=True)
    
    get_target_files_command = f"git log --follow --name-status -- {source_file_path}" 
    to_check_item = run_command(get_target_files_command, repo_dir).splitlines()

    '''    
    Examples: 

    commit 9xxx82b
    Author: yyyy
    Date:   Thu Jul 28 15:28:28 2011 +0100

        HSEARCH-626 - rename BatchLucene* to Batch* as it now applies to all kinds

    R096	hibernate-search/src/main/java/org/hibernate/search/backend/impl/batchlucene/LuceneBatchBackend.java	hibernate-search/src/main/java/org/hibernate/search/backend/impl/batch/DefaultBatchBackend.java

    commit 2dttt80c
    Author: yyyy
    Date:   Thu Jul 28 15:25:20 2011 +0100

        HSEARCH-626 - Simplify BatchBackend, delegating more work to the one and true backend

    M	hibernate-search/src/main/java/org/hibernate/search/backend/impl/batchlucene/LuceneBatchBackend.java
    '''

    if to_check_item:
        # with open(f"{target_commit}.txt", "a") as f:
        #     f.writelines("\n".join(to_check_item) + "\n\n------\n\n")

        target_commit_block_initial = [line_i for line_i, line in enumerate(to_check_item) if target_commit in line]
        if target_commit_block_initial:
            to_check_item = to_check_item[target_commit_block_initial[0]:]
            for line in to_check_item:
                # Added (A), Copied (C), Deleted (D), Modified (M), Renamed (R), 
                # have their type (i.e. regular file, symlink, submodule, …​) changed (T), 
                # are Unmerged (U), are Unknown (X), or have had their pairing Broken (B).
                if re.match(r"^R\d{3}\t", line) or re.match(r"^C\d{3}\t", line):
                    tmp = line.split("\t")
                    target_file_path = tmp[2] # renamed to source file path
                    break
                elif line.startswith("D\t"):
                    target_file_path = "D"
                    break
                elif re.match(r"^[A-Z]\t", line):
                    tmp = line.split("\t")
                    target_file_path = tmp[1] # could be renamed (renamed in another commit, here shows the renamed file path)
                    break
        else:
            # 2 cases:
            # 1. the file is not renamed in nay of the commits, it keeps the sme with sourde file path
            # 2. it renamed at some point, but not at the target commit
            
            candidate_target_file_paths = []
            corres_commits = []
            # get all copies and renames
            for idx, line in enumerate(to_check_item):
                if re.match(r"^R\d{3}\t", line) or re.match(r"^C\d{3}\t", line):
                    corres_commit = None
                    while not corres_commit:
                        idx -= 1
                        tmp_line = to_check_item[idx]
                        if tmp_line.startswith("commit"):
                            corres_commit = tmp_line.split(" ")[1][:8]

                    corres = repo.commit(corres_commit)
                    if corres.committed_date < target.committed_date: # renamed before target commit submitted
                        tmp = line.split("\t")
                        # candidate_target_file_path = tmp[2]
                        candidate_target_file_paths.append(tmp[2])

                        corres_commits.append(corres)
                    else:
                        break
            
            if not corres_commits:
                target_file_path = source_file_path
            elif len(corres_commits) == 1:
                target_file_path = candidate_target_file_paths[0]
            else:
                target_time = datetime.fromtimestamp(target.committed_date)
                time_deltas = [abs(target_time - datetime.fromtimestamp(c.committed_date)) for c in corres_commits]
                min_del = min(time_deltas)
                min_idx = time_deltas.index(min_del)
                # the closest older rename
                target_file_path = candidate_target_file_paths[min_idx]

    return target_file_path