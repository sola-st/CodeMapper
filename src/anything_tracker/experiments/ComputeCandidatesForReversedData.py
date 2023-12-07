from os.path import join
from anything_tracker.experiments.ComputeCandidatesForAllSourceRegions import ComputeCandidatesForAllSourceRegions


if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "candidate_regions_reversed")
    oracle_file = join("data", "oracle", "change_maps_reversed.json")
    is_reversed_data = True
    ComputeCandidatesForAllSourceRegions(oracle_file, result_dir_parent, is_reversed_data).run()