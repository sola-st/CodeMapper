import json
import os
from anything_tracker.multiple.track_histories.AnythingTrackerOnHistoryPairs import main as AnythingTrackerOnHistoryPairs
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join, isdir,exists


class TrackConvertedData():
    """
    Computes candidate region for all the source regions across multiple commits.
    """
    def __init__(self, oracle_history_parent_folder, result_dir_parent, context_line_num, 
                time_file_folder, turn_off_techniques):
        self.oracle_history_parent_folder = oracle_history_parent_folder
        self.result_dir_parent = result_dir_parent
        self.context_line_num = context_line_num
        self.time_file_folder = time_file_folder
        self.turn_off_techniques = turn_off_techniques

    def get_meta_inputs(self):
        """
        Returns a list of parameter list.
        Each inner list contains repo_dir, base_commit, target_commit, file_path, and interest_character_range.
        """
        parameters = []
        time_file_to_write = join(self.time_file_folder, f"execution_time_suppression.csv")
        suppression_repos = os.listdir(self.oracle_history_parent_folder)
        for repo in suppression_repos:
            repo_contents = os.listdir(join(self.oracle_history_parent_folder, repo))
            hist_len = len(repo_contents) - 2
            result_dir_tmp = join(self.result_dir_parent, repo)
            for num_folder in range(hist_len):
                num_folder_str = str(num_folder)
                history_file_path = join(self.oracle_history_parent_folder, repo, \
                        num_folder_str, "expected_full_histories.json")

                with open(history_file_path) as f:
                    histories_pairs = json.load(f)

                assert len(histories_pairs) == 2
                # forward tracking
                source = histories_pairs[0]
                target = histories_pairs[1]

                url = source["url"]
                tmp = url.split("/")
                repo_name = tmp[-1].replace(".git", "")
                repo_dir = join("data", "repos_suppression", repo_name)

                result_dir = join(result_dir_tmp, num_folder_str)

                if not source["range"]:
                    continue
                source_range = json.loads(source["range"])
                parameter = [
                    repo_dir,
                    source["commit"],
                    source["file_path"],
                    target["commit"],
                    source_range,
                    result_dir,
                    self.context_line_num,
                    time_file_to_write,
                    self.turn_off_techniques
                ]
                parameters.append(parameter)

        return parameters

    def run(self):
        # prepare repositories
        repo_urls_file = join("data", "results", "analysis_on_codetracker_data", "source_repos_suppression.txt") # python projects
        repo_folder_suppression = join("data", "repos_suppression")
        source_repo_init = SourceRepos(repo_urls_file, repo_folder_suppression)
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
            # write the target region for the last piece of data
            self.write_target_regions(args_for_all_maps[-1][5], target_regions_for_1_data)

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        ground_truth_results_dir = result_dir.rsplit("/", 1)[0]
        # to handle the case only has 1 history pair and the file is deleted.
        os.makedirs(ground_truth_results_dir, exist_ok=True) 
        target_json_file = join(ground_truth_results_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)
        

if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "latest", "mapped_regions_suppression")
    oracle_history_parent_folder = join("data", "suppression_data")
    time_file_folder = join("data", "results", "execution_time", "latest")
    os.makedirs(time_file_folder, exist_ok=True)
    # context_line_num >=0.
    # 0 means no contexts, >0 means get the corresponding number of lines before and after respectively as contexts
    context_line_num = 0 
    # 3 techniques can be optionally turned off, support turn off one or multiple at a time.
    # 1. move detection  2. search matches  3. fine-grain borders
    turn_off_techniques = [True, False, False] # change the boolean to True to turn off the corresponding technique.
    turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
    TrackConvertedData(oracle_history_parent_folder, result_dir_parent, context_line_num, time_file_folder, turn_off_techniques_obj).run()