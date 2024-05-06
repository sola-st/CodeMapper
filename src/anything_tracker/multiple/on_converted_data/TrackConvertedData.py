import json
from multiprocessing import Pool
from anything_tracker.multiple.on_converted_data.AnythingTrackerOnConvertedData import main as AnythingTrackerOnConvertedData
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join


class TrackConvertedData():
    """
    Computes candidate region for all the source regions across multiple commits.
    """
    def __init__(self, oracle_file, result_dir_parent, context_line_num, 
                time_file_to_write, turn_off_techniques):
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

        # get inputs for computing candidates
        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1].replace(".git", "")
            repo_dir = join("data", "repos_java", repo_name)
            result_dir = join(self.result_dir_parent, str(i))

            source_commit = meta["source_commit"] # start commit
            character_range_list = json.loads(meta["source_range"])
            # category = meta["category"]
            # source_info = meta["source_info"]

            parameter = [
                repo_dir,
                source_commit,
                meta["source_file"],
                character_range_list,
                result_dir,
                self.context_line_num,
                self.time_file_to_write,
                self.turn_off_techniques
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
        
        cores_to_use = 1
        with Pool(processes=cores_to_use) as pool:
            pool.map(self.wrapper, args_for_all_maps)

    def wrapper(self, args):
        AnythingTrackerOnConvertedData(*args)
        source_region_index = args[4].split('/')[-1]
        print(f"Compute candidates is done, source region #{source_region_index}.\n")
        

if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "mapped_regions_convert_test")
    oracle_file = join("data", "converted_data", "converted_data.json")
    time_file_to_write = join("data", "results", "execution_time", "executing_time.csv")
    # context_line_num >=0.
    # 0 means no contexts, >0 means get the corresponding number of lines before and after respectively as contexts
    context_line_num = 0 
    # 3 techniques can be optionally turned off, support turn off one or multiple at a time.
    # 1. move detection  2. search matches  3. fine-grain borders
    turn_off_techniques = [False, False, True] # change the boolean to True to turn off the corresponding technique.
    turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
    TrackConvertedData(oracle_file, result_dir_parent, context_line_num, time_file_to_write, turn_off_techniques_obj).run()