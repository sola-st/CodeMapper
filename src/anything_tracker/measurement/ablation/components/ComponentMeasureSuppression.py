import os
from os.path import join, exists
from anything_tracker.measurement.MeasureSuppression import MeasureSuppression


def main_ablation_study(dataset, oracle_file, results_dir_parent, results_csv_file_folder):
    ablation_settings = ["off_diff", "off_move", "off_search", "off_fine"]
    for setting in ablation_settings:
        results_dir = join(results_dir_parent, f"mapped_regions_{dataset}_{setting}")
        results_csv_file = join(results_csv_file_folder, f"measurement_results_metrics_{dataset}_{setting}.csv")
        MeasureSuppression(oracle_file, results_dir, results_csv_file).run()
        print(f"Measurement: {setting} done.")
    
    results_dir = join(results_dir_parent, f"mapped_regions_{dataset}_off_context") # the default name in experiment, should exists
    results_csv_file = join(results_csv_file_folder, f"measurement_results_metrics_{dataset}_off_context.csv")
    if not exists(results_dir):
        results_dir = join(results_dir_parent, f"mapped_regions_{dataset}_0")
    MeasureSuppression(oracle_file, results_dir, results_csv_file).run()
    print(f"Measurement: off_context done.")

if __name__=="__main__":
    # Run measurement for ablation study (components)
    dataset = "suppression"
    oracle_file_folder = join("data", "suppression_data") # to get the ground truth
    results_dir_parent = join("data", "results", "tracked_maps", dataset) # where the target regions are recorded
    results_csv_file_folder = join("data", "results", "measurement_results", dataset) # to write the measurement results
    os.makedirs(results_csv_file_folder, exist_ok=True)
    main_ablation_study(dataset, oracle_file_folder, results_dir_parent, results_csv_file_folder)