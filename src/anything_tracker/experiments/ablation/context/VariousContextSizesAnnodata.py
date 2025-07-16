from os.path import join
from os import makedirs
from anything_tracker.experiments.TrackHistoryPairsAnnoData import main_anythingtracker


if __name__ == "__main__":
    # Run ablation study about context sizes on annotated data A and B.
    datasets = ["annotation_a", "annotation_b"] # the desired one or two annotated dataset(s)
    turn_off_techniques = [False, False, False, False] 
    for dataset in datasets:
        oracle_file = join("data", "annotation", f"{dataset}_100.json")
        result_dir_parent = join("data", "results", "tracked_maps", dataset)
        time_file_folder = join("data", "results", "execution_time", dataset)
        makedirs(time_file_folder, exist_ok=True)
        '''
        context_line_num should be a num >=0.
        * 0 means no contexts.
        * >0 means get the corresponding number of lines before and after respectively as contexts.
        '''
        context_line_num_list = [0, 1, 2, 3, 5, 10, 20, 25, 30] # without the context_line_num
        for context_line_num in context_line_num_list:
            # context_line_num = 0 --> disable context-aware similarity
            main_anythingtracker(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)
            print(f"[Ablation] context size: {context_line_num}, dataset: {dataset}, Done.\n")