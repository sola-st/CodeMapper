import json
from anything_tracker.multiple.track_histories.AnythingTrackerOnHistoryPairs import main_suppression as AnythingTracker
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs


class ComputeCandidatesForAnnoData():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_file, result_dir_parent, context_line_num, time_file_to_write, turn_off_techniques):
        self.oracle_file = oracle_file
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

        with open(self.oracle_file) as f:
            maps = json.load(f)

        write_mode = "w" # for writing execution times
        # get inputs for computing candidates
        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            result_dir = join(self.result_dir_parent)

            mapping:dict = meta["mapping"]
            character_range_list = json.loads(mapping["source_range"])
            if i != 0:
                write_mode = "a"

            parameter = [
                repo_dir,
                mapping["source_commit"],
                mapping["source_file"],
                mapping["target_commit"],
                character_range_list,
                result_dir,
                self.context_line_num,
                self.time_file_to_write,
                self.turn_off_techniques,
                str(i),
                write_mode
            ]
            parameters.append(parameter)

        return parameters

    def run(self):
        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs()
        for args in args_for_all_maps:
            target_regions_for_1_data = AnythingTracker(*args)
            source_region_index = args[-2]
            print(f"Compute candidates is done, source region #{source_region_index}.\n")
            result_dir_with_num = join(args[5], source_region_index)
            self.write_target_regions(result_dir_with_num, target_regions_for_1_data)

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        makedirs(result_dir, exist_ok=True) 
        target_json_file = join(result_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)


def main_ablation_study(oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques):
    ablation_settings = ["off_all", "off_move", "off_search", "off_fine"]
    for i, setting in enumerate(ablation_settings):
        result_dir = join(result_dir_parent, f"mapped_regions_annodata_{setting}")
        time_file_to_write = join(time_file_folder, f"execution_time_annodata_{setting}.csv")
        if i == 0:
            turn_off_techniques = [True, True, True]
        else:
            turn_off_techniques[i-1] = True
        turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
        ComputeCandidatesForAnnoData(oracle_file, result_dir, context_line_num, time_file_to_write, turn_off_techniques_obj).run()
        turn_off_techniques = [False, False, False] # to start the next iteration

def main_anythingtracker(oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques):
    result_dir = join(result_dir_parent, "mapped_regions_annodata")
    time_file_to_write = join(time_file_folder, "execution_time_annodata.csv")
    turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
    ComputeCandidatesForAnnoData(oracle_file, result_dir, context_line_num, time_file_to_write, turn_off_techniques_obj).run()

if __name__ == "__main__":
    '''
    * context_line_num should be a num >=0.
        0 means no contexts.
        >0 means get the corresponding number of lines before and after respectively as contexts.

    * turn_off_techniques
    There are 3 techniques can be optionally turned off, support turn off one or multiple at a time.
        1. move detection  2. search matches  3. fine-grain borders
        > change the boolean to True to turn off the corresponding technique.
    '''

    oracle_file = join("data", "annotation", "annotations_100.json")
    result_dir_parent = join("data", "results", "tracked_maps", "annodata")
    time_file_folder = join("data", "results", "execution_time", "annodata")
    makedirs(time_file_folder, exist_ok=True)
    context_line_num = 2 
    turn_off_techniques = [False, False, False] 

    # Run AnythingTracker
    main_anythingtracker(oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)
    # Run ablation study
    main_ablation_study(oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)