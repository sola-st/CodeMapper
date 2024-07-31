import subprocess


def get_target_file_path(repo_dir, source_commit, target_commit, source_file_path):
    # renamed_file_path = None
    # file_is_deleted = False
    to_return = source_file_path # it can be renamed_file_path or file_is_deleted
    to_track_new_path = ("R", "C")

    # If the file is deleted, the target commit has no corresponding character range.
    # If the file is renamed/copied, we track it in the new file path.
    get_renamed_files_command = f"git diff --name-status --diff-filter=DRC {source_commit} {target_commit}"
    renamed_result = subprocess.run(get_renamed_files_command, cwd=repo_dir, shell=True,
        stdout=subprocess.PIPE, universal_newlines=True)
    to_check_items = renamed_result.stdout

    if to_check_items:
        to_check_list = to_check_items.strip().split("\n")
        for to_check in to_check_list:
            # R094    src/traverse.py src/common/traverse.py
            tmp = to_check.split("\t")
            if tmp[1] == source_file_path:
                if to_check.startswith(to_track_new_path):
                    to_return = tmp[2]
                else: # D
                    to_return = True
                break

    return to_return