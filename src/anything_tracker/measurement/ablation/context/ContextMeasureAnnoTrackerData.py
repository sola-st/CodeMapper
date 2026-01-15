import os
from os.path import join, exists
from anything_tracker.measurement.MeasureAnnoTrackerData import MeasureAnnotatedData


def main_ablation_study_context_size(dataset, oracle_file, results_dir_parent, results_csv_file_folder):
    context_line_num_list = [0, 1, 2, 3, 5, 10, 20, 25, 30] # without the default context size
    for num in context_line_num_list:
        results_dir = join(results_dir_parent, f"mapped_regions_{dataset}_{num}")
        if num == 0: 
            results_dir = results_dir if exists(results_dir) else join(results_dir_parent, f"mapped_regions_{dataset}_off_context")
        # this could be a duplicated with 'measurement_results_metrics_{dataset}_0', 
        # since we do not know the order of these two ablations studies, keep both of them
        results_csv_file = join(results_csv_file_folder, f"measurement_results_metrics_{dataset}_{num}.csv")
        MeasureAnnotatedData(dataset, oracle_file, results_dir, results_csv_file).run()
        print(f"Measurement: context size {num} done.")


if __name__=="__main__":
    # Run measurement for ablation study (context sizes)
    datasets = ["annotation_a", "annotation_b", "variable_test", "block_test", "method_test"]
    for dataset in datasets:
        oracle_file = join("data", "annotation", f"{dataset}.json") # to get the ground truth
        results_dir_parent = join("data", "results", "tracked_maps", dataset) # where the target regions are recorded
        results_csv_file_folder = join("data", "results", "measurement_results", dataset) # to write the measurement results
        os.makedirs(results_csv_file_folder, exist_ok=True)
        main_ablation_study_context_size(dataset, oracle_file, results_dir_parent, results_csv_file_folder)