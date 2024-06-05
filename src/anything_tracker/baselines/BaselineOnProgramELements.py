import json
from anything_tracker.baselines.BaselineTracker import main as AnythingTracker
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs, listdir
from anything_tracker.multiple.track_histories.TrackHistoryPairs import get_category_subfolder_info


class BaselineOnProgramELements():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_history_parent_folder, result_dir_parent, time_file_folder, level):
        self.oracle_history_parent_folder = oracle_history_parent_folder
        self.result_dir_parent = result_dir_parent
        self.time_file_folder = time_file_folder
        self.level = level
        
    def get_meta_inputs(self):
        parameters = []
        category_subset_pairs = get_category_subfolder_info(self.oracle_history_parent_folder)
        # category_subset_pairs = [["variable", "training"]]
        for category, subset in category_subset_pairs: # eg., method, test
            time_file_to_write = join(self.time_file_folder, f"execution_time_{category}_{subset}_{self.level}.csv")
            subset_folder = join(self.oracle_history_parent_folder, category, subset)
            subset_folder_len = len(listdir(subset_folder))
            subset_result_dir = join(f"{self.result_dir_parent}_{category}_{subset}")
            for num_folder in range(subset_folder_len):
                num_folder_str = str(num_folder)
                history_file_path = join(self.oracle_history_parent_folder, category, subset,\
                        num_folder_str, "expect_full_histories.json")

                with open(history_file_path) as f:
                    histories_pairs = json.load(f)

                result_dir_parent_tmp = join(subset_result_dir, num_folder_str)
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
                    if meta["target_range"] == "None":
                        continue
                    character_range_list = json.loads(meta["target_range"])
                    # TODO check the converted data
                    if not character_range_list or \
                        (character_range_list[1] == character_range_list[3]) and (character_range_list[0] == character_range_list[2]):
                        continue
                    target_commit = meta["source_commit"]
                    if target_commit == "0": # the initial commit
                        continue

                    parameter = [
                        self.level,
                        repo_dir,
                        source_commit,
                        meta["target_file"], # means source file
                        target_commit,
                        character_range_list,
                        result_dir,
                        time_file_to_write
                    ]
                    parameters.append(parameter)

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
            result_dir = args[6]
            tmp = result_dir.split('/')
            history_pair_index = int(tmp[-1])

            if refer_idx + 1 != history_pair_index:
                if target_regions_for_1_data:
                    self.write_target_regions(args_for_all_maps[i-1][6], target_regions_for_1_data)
                    target_regions_for_1_data = []
                    source_region_index = tmp[-2]
                    print(f"Compute candidates done, source region #{source_region_index}.\n")

            refer_idx = history_pair_index
            dist_based = AnythingTracker(*args)
            target_regions_for_1_data.extend(dist_based)

        if target_regions_for_1_data:
            # write the target region for the last peice of data
            self.write_target_regions(args_for_all_maps[-1][6], target_regions_for_1_data)

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        ground_truth_results_dir = result_dir.rsplit("/", 1)[0]
        # to handle the case only has 1 history pair and the file is deleted.
        makedirs(ground_truth_results_dir, exist_ok=True) 
        target_json_file = join(ground_truth_results_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "element", "line", "mapped_regions_element_line")
    oracle_history_parent_folder = join("data", "converted_data")
    time_file_folder = join("data", "results", "execution_time", "element", "line")
    makedirs(time_file_folder, exist_ok=True)
    level = "line"
    BaselineOnProgramELements(oracle_history_parent_folder, result_dir_parent, time_file_folder, level).run()