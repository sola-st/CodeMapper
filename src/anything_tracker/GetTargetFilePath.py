import subprocess
from git import Repo
import re


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
        # with open(f"{target_commit}.txt", "w") as f:
        #     f.writelines("\n".join(to_check_item))

        target_commit_block_initial = [line_i for line_i, line in enumerate(to_check_item) if target_commit in line]
        if target_commit_block_initial:
            to_check_item = to_check_item[target_commit_block_initial[0]:]
            for line in to_check_item:
                # Added (A), Copied (C), Deleted (D), Modified (M), Renamed (R), 
                # have their type (i.e. regular file, symlink, submodule, …​) changed (T), 
                # are Unmerged (U), are Unknown (X), or have had their pairing Broken (B).
                if re.match(r"^R\d{3}\t", line) or re.match(r"^C\d{3}\t", line):
                    tmp = line.split("\t")
                    # if tmp[2] == source_file_path: # not always
                    target_file_path = tmp[2] # renamed to source file path
                    break
                elif line.startswith("D\t"):
                    target_file_path = "D"
                    break
                elif re.match(r"^[A-Z]\t", line):
                    tmp = line.split("\t")
                    target_file_path = tmp[1] # could be renamed (renamed inbanother commit, here shows the renamed file path)
                    break
        else:
            target_file_path = source_file_path

    return target_file_path