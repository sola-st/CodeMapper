import json
from multiprocessing import Pool, cpu_count
from anything_tracker.AnythingTracker import AnythingTracker
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join

from anything_tracker.utils.RepoUtils import get_parent_commit


class ComputeCandidatesForAllSourceRegions():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_file, result_dir_parent, is_data_reversed=False):
        self.oracle_file = oracle_file
        self.result_dir_parent = result_dir_parent
        # False --> original data
        # True --> reversed data
        self.is_data_reversed = is_data_reversed 

    def get_base_target_commit_ids(self, repo_dir, child_commit):
        parent_commit = get_parent_commit(repo_dir, child_commit)
        if self.is_data_reversed == True:
            return child_commit, parent_commit
        else:
            return parent_commit, child_commit
        
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
            repo_name = tmp[-3]
            child_commit = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            base_commit, target_commit = self.get_base_target_commit_ids(repo_dir, child_commit)
            assert base_commit != ""
            result_dir = join(self.result_dir_parent, str(i))

            mapping:dict = meta["mapping"]
            if mapping["source_range"] == None:
                continue

            character_range_list = json.loads(mapping["source_range"])
            parameter = [
                repo_dir,
                base_commit,
                target_commit,
                mapping["source_file"],
                character_range_list,
                result_dir
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
        
        # TODO Solve the conflicts that checkout a repo to different commits at the same time.
        # cores_to_use = cpu_count() - 1 # leave one core for other processes
        cores_to_use = 1
        print(f"Using {cores_to_use} cores in parallel.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(wrapper, args_for_all_maps)

def wrapper(args):
    AnythingTracker(*args).run()
    source_region_index = args[-2].split('/')[-1]
    print(f"Compute candidates is done, source region #{source_region_index}.")