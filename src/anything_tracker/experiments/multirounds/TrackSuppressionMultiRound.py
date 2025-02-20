from os.path import join
from os import makedirs
from anything_tracker.experiments.ComputeCandidatesForAnnoData import main_anythingtracker


if __name__ == "__main__":
    '''
    Run multiple rounds of the experiment:
     * Tracking suppression data
    '''

    dataset = "suppression"
    oracle_history_parent_folder = join("data", "suppression_data")
    context_line_num = 15 
    turn_off_techniques = [False, False, False, False] 
    for i in range(2, 6):
        result_dir_parent = join("data", "results", "tracked_maps", f"round_{i}", dataset)
        time_file_folder = join("data", "results", "execution_time", f"round_{i}", dataset)
        makedirs(time_file_folder, exist_ok=True)
        main_anythingtracker(dataset, oracle_history_parent_folder, result_dir_parent, \
                time_file_folder, context_line_num, turn_off_techniques)
        print(f"[Multi-round] Round: {i} (no round_0), dataset: {dataset}, Done.\n")
