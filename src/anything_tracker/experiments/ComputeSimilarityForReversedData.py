from os.path import join       
from anything_tracker.experiments.ComputeSimilarityOnAllResults import ComputeSimilarityOnAllResults


if __name__ == "__main__":
    results_parent_dir = join("data", "results", "tracked_maps", "candidate_regions_reversed")
    measurement_csv_file = join("data", "results", "measurement_results_reversed.csv")
    ComputeSimilarityOnAllResults(results_parent_dir, measurement_csv_file).run()