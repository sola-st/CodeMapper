import json
import os
from anything_tracker.multiple.track_histories.AnythingTrackerOnHistoryPairs import main as AnythingTrackerOnHistoryPairs
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join, isdir,exists


def get_category_subfolder_info(parent_folder):
    category_subset_pairs = []
    subfolders = ["test", "training"]

    folders = os.listdir(parent_folder)
    for folder in folders:
        category_folder = join(parent_folder, folder)
        if isdir(category_folder):
            exists_num = 0
            for f in subfolders:
                if exists(join(category_folder, f)) == True:
                    exists_num+=1
            if exists_num == 2:
                for f in subfolders:
                    category_subset_pairs.append([folder, f])

    return category_subset_pairs


class TrackConvertedData():
    """
    Computes candidate region for all the source regions across multiple commits.
    """
    def __init__(self, oracle_history_parent_folder, result_dir_parent, context_line_num, 
                time_file_to_write, turn_off_techniques):
        self.oracle_history_parent_folder = oracle_history_parent_folder
        self.result_dir_parent = result_dir_parent
        self.context_line_num = context_line_num
        self.time_file_to_write = time_file_to_write
        self.turn_off_techniques = turn_off_techniques

    def get_meta_inputs(self):
        """
        Returns a list of parameter list.
        Each inner list contains repo_dir, base_commit, target_commit, file_path, and interest_character_range.
        """
        parameters = []
        category_subset_pairs = get_category_subfolder_info(self.oracle_history_parent_folder)
        # category_subset_pairs = [["method", "test"]]
        for category, subset in category_subset_pairs: # eg., method, test
            subset_folder = join(self.oracle_history_parent_folder, category, subset)
            subset_folder_len = len(os.listdir(subset_folder))
            for num_folder in range(subset_folder_len):
                num_folder_str = str(num_folder)
                history_file_path = join(self.oracle_history_parent_folder, category, subset,\
                        num_folder_str, "expect_full_histories.json")

                with open(history_file_path) as f:
                    histories_pairs = json.load(f)

                result_dir_parent_tmp = join(self.result_dir_parent, num_folder_str)
                # get inputs for computing candidates
                # Note: here the keys are special for converted code tracker data
                for i, meta in enumerate(histories_pairs):
                    url = meta["url"]
                    tmp = url.split("/")
                    repo_name = tmp[-1].replace(".git", "")
                    repo_dir = join("data", "repos_java", repo_name)
                    result_dir = join(result_dir_parent_tmp, str(i)) #eg., maps/0/0-11

                    # here target commit is the newer commit,
                    # and we use it as source commit for backward tracking, 
                    source_commit = meta["target_commit"]
                    character_range_list = json.loads(meta["target_range"])

                    parameter = [
                        repo_dir,
                        source_commit,
                        meta["target_file"],
                        meta["source_commit"],
                        character_range_list,
                        result_dir,
                        self.context_line_num,
                        self.time_file_to_write,
                        self.turn_off_techniques
                    ]
                    parameters.append(parameter)

                if num_folder == 1:
                    break

        return parameters

    def run(self):
        # prepare repositories
        repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_java.txt")
        repo_folder_java = join("data", "repos_java")
        source_repo_init = SourceRepos(repo_urls_file, repo_folder_java)
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs()
        refer_idx = -1
        target_regions_for_1_data = []

        for i, args in enumerate(args_for_all_maps):
            result_dir = args[5]
            tmp = result_dir.split('/')
            history_pair_index = int(tmp[-1])

            if refer_idx + 1 != history_pair_index:
                if target_regions_for_1_data:
                    self.write_target_regions(args_for_all_maps[i-1][5], target_regions_for_1_data)
                    target_regions_for_1_data = []
                    source_region_index = tmp[-2]
                    print(f"Compute candidates done, source region #{source_region_index}.\n")

            refer_idx = history_pair_index
            dist_based = AnythingTrackerOnHistoryPairs(*args)
            target_regions_for_1_data.extend(dist_based)

        if target_regions_for_1_data:
            # write the target region for the last peice of data
            self.write_target_regions(args_for_all_maps[-1][5], target_regions_for_1_data)

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        ground_truth_results_dir = result_dir.rsplit("/", 1)[0]
        target_json_file = join(ground_truth_results_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)
        

if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "mapped_regions")
    oracle_history_parent_folder = join("data", "converted_data")
    time_file_to_write = join("data", "results", "execution_time", "executing_time.csv")
    # context_line_num >=0.
    # 0 means no contexts, >0 means get the corresponding number of lines before and after respectively as contexts
    context_line_num = 0 
    # 3 techniques can be optionally turned off, support turn off one or multiple at a time.
    # 1. move detection  2. search matches  3. fine-grain borders
    turn_off_techniques = [False, False, True] # change the boolean to True to turn off the corresponding technique.
    turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
    TrackConvertedData(oracle_history_parent_folder, result_dir_parent, context_line_num, time_file_to_write, turn_off_techniques_obj).run()