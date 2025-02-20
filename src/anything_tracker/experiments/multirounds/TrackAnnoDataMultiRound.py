from os.path import join
from os import makedirs
from anything_tracker.experiments.ComputeCandidatesForAnnoData import main_anythingtracker


if __name__ == "__main__":
    '''
    Run multiple rounds of the following experiments:
     * Tracking annotated data A
     * Tracking annotated data B
    '''
    datasets = ["annotation_a", "annotation_b"] 
    context_line_num = 15 
    turn_off_techniques = [False, False, False, False] 
    for dataset in datasets:
        oracle_file = join("data", "annotation", f"{dataset}_100.json")
        for i in range(2, 6): # default to run additional four rounds
            result_dir_parent = join("data", "results", "tracked_maps", f"round_{i}", dataset)
            time_file_folder = join("data", "results", "execution_time", f"round_{i}", dataset)
            makedirs(time_file_folder, exist_ok=True)
            main_anythingtracker(dataset, oracle_file, result_dir_parent, \
                    time_file_folder, context_line_num, turn_off_techniques)
            print(f"[Multi-round] Round: {i} (no round_0), dataset: {dataset}, Done.\n")
