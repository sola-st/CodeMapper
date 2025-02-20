from os.path import join
from os import makedirs
from anything_tracker.experiments.TrackHistoryPairsSuppression import main_anythingtracker


if __name__ == "__main__":
    # Run ablation study about context sizes on suppression data.
    dataset = "suppression"
    oracle_history_parent_folder = join("data", "suppression_data")
    result_dir_parent = join("data", "results", "tracked_maps", dataset)
    time_file_folder = join("data", "results", "execution_time", dataset) 
    makedirs(time_file_folder, exist_ok=True)
    turn_off_techniques = [False, False, False, False] 
    '''
    context_line_num should be a num >=0.
     * 0 means no contexts.
     * >0 means get the corresponding number of lines before and after respectively as contexts.
    '''
    context_line_num_list = [0, 1, 2, 3, 5, 10, 20, 25, 30] # without the context_line_num
    for context_line_num in context_line_num_list:
        # context_line_num = 0 --> disable context-aware similarity
        main_anythingtracker(dataset, oracle_history_parent_folder, \
                result_dir_parent, time_file_folder, context_line_num, turn_off_techniques) 