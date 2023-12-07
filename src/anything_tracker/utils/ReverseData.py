import json
from os.path import join

from anything_tracker.utils.RepoUtils import get_parent_commit


def reverse_data():
    # read maps file
    oracle_file = join("data", "oracle", "change_maps.json")
    with open(oracle_file) as f:
        maps = json.load(f)
    
    # read maps and reverse it
    reversed_data = []
    for i, meta in enumerate(maps):
        url = meta["url"]
        tmp = url.split("/")
        repo_name = tmp[-3]
        target_commit = tmp[-1]
        repo_dir = join("data", "repos", repo_name)
        base_commit = get_parent_commit(repo_dir, target_commit)
        assert base_commit != ""
        mapping:dict = meta["mapping"]
        '''
        all change operation markers:
            1) intra-line modify
            2) modify
            3) delete
            4) add
            5) move
            6) modify and move
            7) insert 1 line
        only 3), 4) and 7) need to be reversed
        '''
        change_operation = mapping["change_operation"]
        if change_operation == "add":
            change_operation = "delete"
        elif change_operation == "delete":
            change_operation = "add" 
        elif change_operation == "insert 1 line":
            change_operation == "drop 1 line"

        reverse = {
            "url": url,
            "mapping": {
                "source_file": mapping["target_file"],
                "target_file": mapping["source_file"],
                "source_range": mapping["target_range"],
                "target_range": mapping["source_range"],
                "change_operation": change_operation,
                "kind": mapping["kind"]
            }
        }
        reversed_data.append(reverse)

    reversed_oracle_file = oracle_file.replace(".json", "_reversed.json")
    with open(reversed_oracle_file, "w") as ds:
        json.dump(reversed_data, ds, indent=4, ensure_ascii=False)


if __name__=="__main__":
    reverse_data()