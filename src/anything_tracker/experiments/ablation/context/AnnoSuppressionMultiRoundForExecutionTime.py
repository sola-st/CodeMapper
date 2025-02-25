from os.path import join
from os import makedirs
from anything_tracker.experiments.ComputeCandidatesForAnnoData import main_anythingtracker as anno
from anything_tracker.experiments.TrackHistoryPairsSuppression import main_anythingtracker as suppression


if __name__ == "__main__":
    # Multiple rounds for context size with 5 and 10.
    datasets = ["annotation_a", "annotation_b", "suppression"] # the desired dataset(s)  
    turn_off_techniques = [False, False, False, False] 
    context_line_num_list = [5, 10]
    for i in range(2, 6):
        for dataset in datasets:
            if dataset == "suppression":
                oracle_file = join("data", "suppression_data") # a folder
            else:
                oracle_file = join("data", "annotation", f"{dataset}_100.json")
            for context_line_num in context_line_num_list:
                result_dir_parent = join("data", "results", "tracked_maps", f"round_{i}", dataset)
                time_file_folder = join("data", "results", "execution_time", f"round_{i}", dataset)
                makedirs(time_file_folder, exist_ok=True)
                if dataset == "suppression":
                    suppression(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)
                else:
                    anno(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)
                print(f"[Multi-round] context size: {context_line_num}, dataset: {dataset}, Done.\n")
    