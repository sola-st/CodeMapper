import json
from anything_tracker.baselines.BaselineTracker import main_suppression_annodata as AnythingTracker
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs, listdir


class BaselineOnSuprression():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_history_parent_folder, result_dir_parent, time_file_to_write, level):
        self.oracle_history_parent_folder = oracle_history_parent_folder
        self.result_dir_parent = result_dir_parent
        self.time_file_to_write = time_file_to_write
        self.level = level
        
    def get_meta_inputs(self, repo_dirs):
        write_mode = "w"
        write_mode_write_new_file = True
        parameters = []
        for repo_dir in repo_dirs:
            repo = repo_dir.split("/")[-1]
            repo_contents = listdir(join(self.oracle_history_parent_folder, repo))
            hist_len = len(repo_contents)
            result_dir = join(self.result_dir_parent, repo)
            for num_folder in range(hist_len):
                num_folder_str = str(num_folder)
                history_file_path = join(self.oracle_history_parent_folder, repo, \
                        num_folder_str, "expect_full_histories.json")
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

                if not source["range"]:
                    continue
                source_range = json.loads(source["range"])
                    
                parameter = [
                    self.level,
                    repo_dir,
                    source["commit"],
                    source["file_path"],
                    target["commit"],
                    source_range,
                    result_dir,
                    self.time_file_to_write,
                    num_folder_str,
                    write_mode
                ]
                parameters.append(parameter)

                if write_mode_write_new_file == True:
                    write_mode = "a"
                    write_mode_write_new_file = False

        return parameters
    

    def run(self):
        # prepare repositories
        repo_urls_file = join("data", "python_repos.txt")
        repo_folder_suppression = join("data", "repos_suppression")
        source_repo_init = SourceRepos(repo_urls_file, repo_folder_suppression)
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs(repo_dirs)
        target_regions_for_1_data = []
        refer_result_dir = args_for_all_maps[0][6]

        for args in args_for_all_maps:
            result_dir = args[6]
            if refer_result_dir != result_dir: # write results for current repo
                repo_name = refer_result_dir.rsplit("/", 1)[1]
                self.write_target_regions(refer_result_dir, target_regions_for_1_data)
                print(f"*A* Compute candidates done, #{repo_name} **.\n")
                refer_result_dir = result_dir
                target_regions_for_1_data = []

            dist_based = AnythingTracker(*args)
            target_regions_for_1_data.extend(dist_based)

        if target_regions_for_1_data:
            # write the target region for the last repo
            result_dir = args_for_all_maps[-1][6]
            repo_name = result_dir.rsplit("/", 1)[1]
            self.write_target_regions(result_dir, target_regions_for_1_data)
            print(f"*Z* Compute candidates done, #{repo_name} **.\n")

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        makedirs(result_dir, exist_ok=True) 
        target_json_file = join(result_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    levels = ["line", "word"]
    for level in levels:
        result_dir_parent = join("data", "results", "tracked_maps", "suppression", f"mapped_regions_suppression_{level}")
        oracle_history_parent_folder = join("data", "suppression_data")
        time_file_folder = join("data", "results", "execution_time", "suppression")
        makedirs(time_file_folder, exist_ok=True)
        time_file_to_write = join(time_file_folder, f"execution_time_suppression_{level}.csv")
        BaselineOnSuprression(oracle_history_parent_folder, result_dir_parent, time_file_to_write, level).run()
        print(f"Baseline {level} level done.")