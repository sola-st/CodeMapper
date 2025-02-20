from os.path import join
from os import makedirs
from anything_tracker.baselines.BaselineOnAnnoData import BaselineOnAnnoData


if __name__ == "__main__":
    '''
    This is the entry of running multiple rounds of the tracking.
    The file for normally run the exeperiment is: baselines.BaselineOnAnnoData.py,
        - run it to get the default/orinal/1st round.
    Here run several more rounds to get the everage execution time.
    '''
    datasets = ["annotation_a", "annotation_b"]
    levels = ["line", "word"]
    for i in range(2, 6): # run four more rounds
        for dataset in datasets:
            for level in levels:
                result_dir_parent = join("data", "results", "tracked_maps", f"round_{i}", dataset, f"mapped_regions_{dataset}_{level}")
                oracle_file = join("data", "annotation", f"{dataset}_100.json")
                time_file_folder = join("data", "results", "execution_time", f"round_{i}", dataset)
                makedirs(time_file_folder, exist_ok=True)
                time_file_to_write = join(time_file_folder, f"execution_time_{dataset}_{level}.csv")
                BaselineOnAnnoData(oracle_file, result_dir_parent, time_file_to_write, level).run()
                print(f"Round {i}, Baseline {level} level done for {dataset}.\n")