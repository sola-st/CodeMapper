import datetime
import json
from multiprocessing import Pool
from anything_tracker.AnythingTracker import AnythingTracker
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join


class ComputeCandidatesForAnnoData():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_file, result_dir_parent, context_line_num, is_data_reversed=False):
        self.oracle_file = oracle_file
        self.result_dir_parent = result_dir_parent
        self.context_line_num = context_line_num
        # False --> original data
        # True --> reversed data
        self.is_data_reversed = is_data_reversed 
        
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
            repo_name = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            result_dir = join(self.result_dir_parent, str(i))

            mapping:dict = meta["mapping"]
            character_range_list = json.loads(mapping["source_range"])
            parameter = [
                repo_dir,
                mapping["source_commit"],
                mapping["target_commit"],
                mapping["source_file"],
                character_range_list,
                result_dir,
                self.context_line_num
            ]
            expected_character_range_list = None
            if mapping["target_range"] != None:
                expected_character_range_list = json.loads(mapping["target_range"])
            parameter.append(expected_character_range_list)
            parameters.append(parameter)

        return parameters

    def run(self):
        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs()
        
        cores_to_use = 1
        with Pool(processes=cores_to_use) as pool:
            pool.map(wrapper, args_for_all_maps)

def wrapper(args):
    start_time = datetime.datetime.now()
    AnythingTracker(*args).run()
    source_region_index = args[-3].split('/')[-1]
    print(f"Compute candidates is done, source region #{source_region_index}.")
    end_time = datetime.datetime.now()
    executing_time = (end_time - start_time).seconds
    print(f"Executing time: {executing_time} seconds")

if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "mapped_regions")
    oracle_file = join("data", "annotation", "annotations_100.json")
    # context_line_num >=0.
    # 0 means no contexts, >0 means get the corresponding number of lines before and after respectively as contexts
    context_line_num = 0 
    ComputeCandidatesForAnnoData(oracle_file, result_dir_parent, context_line_num).run()