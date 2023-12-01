import json
from multiprocessing import Pool, cpu_count
import os
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.AnythingTracker import main as AnythingTracker
from os.path import join

from anything_tracker.utils.RepoUtils import get_parent_commit


class ComputeCandidatesForAllSourceRegions():
    """
    Computes candidate region for all the source regions.
    """
    def get_meta_inputs(self):
        """
        Returns a list of parameter list.
        Each inner list contains repo_dir, base_commit, target_commit, file_path, and interest_character_range.
        """
        # create output folder
        results_dir = join("data", "results", "tracked_maps/candidate_regions")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        parameters = []

        # read maps file
        oracle_file = join("data", "oracle", "change_maps.json")
        with open(oracle_file) as f:
            maps = json.load(f)

        # get inputs for 
        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-3]
            target_commit = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            base_commit = get_parent_commit(repo_dir, target_commit)
            assert base_commit != ""

            result_file = join(results_dir, f"results_{i}.json")

            mapping:dict = meta["mapping"]
            # TODO Change the oracle, or cover these cases.
            if mapping["old_range"] == None:
                continue
            character_range_list = json.loads(mapping["old_range"])

            parameter = [
                repo_dir,
                base_commit,
                target_commit,
                mapping["old_file"],
                character_range_list,
                result_file
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
        
        # TODO Solve the conflicts that checkout a repo to different commits at the same time.
        # cores_to_use = cpu_count() - 1 # leave one core for other processes
        cores_to_use = 1
        print(f"Using {cores_to_use} cores in parallel.")
        with Pool(processes=cores_to_use) as pool:
            pool.map(wrapper, args_for_all_maps)

def wrapper(args):
    AnythingTracker(*args)

if __name__ == "__main__":
    ComputeCandidatesForAllSourceRegions().run()