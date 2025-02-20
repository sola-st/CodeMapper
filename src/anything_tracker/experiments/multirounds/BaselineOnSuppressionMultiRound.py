from os.path import join
from os import makedirs
from anything_tracker.baselines.BaselineOnSuppression import BaselineOnSuprression


if __name__ == "__main__":
    levels = ["line", "word"]
    for i in range(2, 6):     
        for level in levels:
            result_dir_parent = join("data", "results", "tracked_maps", f"round_{i}", "suppression", f"mapped_regions_suppression_{level}")
            oracle_history_parent_folder = join("data", "suppression_data")
            time_file_folder = join("data", "results", "execution_time", f"round_{i}", "suppression")
            makedirs(time_file_folder, exist_ok=True)
            time_file_to_write = join(time_file_folder, f"execution_time_suppression_{level}.csv")
            BaselineOnSuprression(oracle_history_parent_folder, result_dir_parent, time_file_to_write, level).run()
            print(f"Baseline {level} level, round {i} done.\n")