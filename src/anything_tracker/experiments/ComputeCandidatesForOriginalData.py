from os.path import join
from anything_tracker.experiments.ComputeCandidatesForAllSourceRegions import ComputeCandidatesForAllSourceRegions


if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "candidate_regions")
    oracle_file = join("data", "oracle", "change_maps.json")
    # is_reversed_data = False
    ComputeCandidatesForAllSourceRegions(oracle_file, result_dir_parent).run()