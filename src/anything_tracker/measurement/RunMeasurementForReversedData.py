from os.path import join
from anything_tracker.measurement.RunMeasurement import RunMeasurement


if __name__=="__main__":
    oracle_file = join("data", "oracle", "change_maps_reversed.json")
    candidates_dir = join("data", "results", "tracked_maps", "candidate_regions_reversed")
    results_csv_file_name = "measurement_results_reversed.csv"
    RunMeasurement(oracle_file, candidates_dir, results_csv_file_name).run()