import json
import os
from anything_tracker.AnythingTrackerOnHistoryPairs import main_suppression as AnythingTrackerOnHistoryPairs
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join


class TrackHistoryPairsSuppression():
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

    def get_meta_inputs(self, repo_dirs):
        """
        Returns a list of parameter list.
        Each inner list contains repo_dir, base_commit, target_commit, file_path, and interest_character_range.
        """

        write_mode = "w"
        write_mode_write_new_file = True
        parameters = []
        for repo_dir in repo_dirs:
            repo = repo_dir.split("/")[-1]
            repo_contents = os.listdir(join(self.oracle_history_parent_folder, repo))
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
                    repo_dir,
                    source["commit"],
                    source["file_path"],
                    target["commit"],
                    source_range,
                    result_dir,
                    self.context_line_num,
                    self.time_file_to_write,
                    self.turn_off_techniques,
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
        repo_urls_file = join("data", "python_repos.txt") # python projects
        repo_folder_suppression = join("data", "repos_suppression")
        source_repo_init = SourceRepos(repo_urls_file, repo_folder_suppression)
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs(repo_dirs)
        target_regions_for_1_data = []
        refer_result_dir = args_for_all_maps[0][5]

        for args in args_for_all_maps:
            result_dir = args[5]
            if refer_result_dir != result_dir: # write results for current repo
                repo_name = refer_result_dir.rsplit("/", 1)[1]
                self.write_target_regions(refer_result_dir, target_regions_for_1_data)
                print(f"*A* Compute candidates done, #{repo_name} **.\n")
                refer_result_dir = result_dir
                target_regions_for_1_data = []

            dist_based = AnythingTrackerOnHistoryPairs(*args)
            target_regions_for_1_data.extend(dist_based)
            # print(f"Compute candidates done, source region #{args[-1]}.\n")

        if target_regions_for_1_data:
            # write the target region for the last repo
            result_dir = args_for_all_maps[-1][5]
            repo_name = result_dir.rsplit("/", 1)[1]
            self.write_target_regions(result_dir, target_regions_for_1_data)
            print(f"*Z* Compute candidates done, #{repo_name} **.\n")

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        # to handle the case only has 1 history pair and the file is deleted.
        os.makedirs(result_dir, exist_ok=True) 
        target_json_file = join(result_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)

def main_ablation_study(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques):
    ablation_settings = ["off_diff", "off_move", "off_search", "off_fine"]
    for i, setting in enumerate(ablation_settings):
        result_dir = join(result_dir_parent, f"mapped_regions_{dataset}_{setting}")
        time_file_to_write = join(time_file_folder, f"execution_time_{dataset}_{setting}.csv")
        turn_off_techniques[i] = True
        turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
        TrackHistoryPairsSuppression(oracle_file, result_dir, context_line_num, time_file_to_write, turn_off_techniques_obj).run()
        turn_off_techniques = [False, False, False, False] # to start the next iteration

def main_anythingtracker(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques, context_ablation=False):
    result_dir = join(result_dir_parent, f"mapped_regions_{dataset}_{context_line_num}")
    time_file_to_write = join(time_file_folder, f"execution_time_{dataset}_{context_line_num}_not_in_figure.csv")
    if context_ablation == True: # add the context_line_num to recognize different versions.
        result_dir = f"result_dir_{context_line_num}"
        time_file_to_write = time_file_to_write.replace(".csv", f"_{context_line_num}.csv")
    else:
        if context_line_num == 0: # ablation study of techniques
            result_dir = f"{result_dir}_off_context"
            time_file_to_write = time_file_to_write.replace(".csv", "_off_context.csv")
    turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
    TrackHistoryPairsSuppression(oracle_file, result_dir, context_line_num, time_file_to_write, turn_off_techniques_obj).run()

if __name__ == "__main__":
    '''
    * context_line_num should be a num >=0.
        0 means no contexts.
        >0 means get the corresponding number of lines before and after respectively as contexts.

    * turn_off_techniques
    There are 4 techniques can be optionally turned off, support turn off one or multiple at a time.
        0. diff-based candidate computation  1. move detection  2. search matches  3. fine-grain borders
        > change the boolean to True to turn off the corresponding technique.
    '''

    dataset = "suppression"
    oracle_history_parent_folder = join("data", "suppression_data")
    result_dir_parent = join("data", "results", "tracked_maps", dataset)
    time_file_folder = join("data", "results", "execution_time", dataset) 
    os.makedirs(time_file_folder, exist_ok=True)
    context_line_num = 15 
    turn_off_techniques = [False, False, False, False] 

    # Three options to start experiments:
    # 1.Run AnythingTracker
    main_anythingtracker(dataset, oracle_history_parent_folder, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)

    # 2. Run ablation study (about techniques)
    main_ablation_study(dataset, oracle_history_parent_folder, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques) 
    
    # 3. Run ablation study (about context sizes)
    context_line_num_list = [0, 1, 2, 3, 5, 10, 15, 20, 25, 30] 
    for context_line_num in context_line_num_list:
        # context_line_num = 0 --> disable context-aware similarity
        main_anythingtracker(dataset, oracle_history_parent_folder, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques, True)     