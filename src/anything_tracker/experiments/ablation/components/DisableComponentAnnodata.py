from os.path import join
from os import makedirs
from anything_tracker.SpecifyToTurnOffTechniques import SpecifyToTurnOffTechniques
from anything_tracker.experiments.TrackHistoryPairsAnnoData import ComputeCandidatesForAnnoData


def main_ablation_study(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques):
    ablation_settings = ["off_diff", "off_move", "off_search", "off_fine"]
    for i, setting in enumerate(ablation_settings):
        result_dir = join(result_dir_parent, f"mapped_regions_{dataset}_{setting}")
        time_file_to_write = join(time_file_folder, f"execution_time_{dataset}_{setting}.csv")
        turn_off_techniques[i] = True
        turn_off_techniques_obj = SpecifyToTurnOffTechniques(turn_off_techniques)
        ComputeCandidatesForAnnoData(oracle_file, result_dir, context_line_num, time_file_to_write, turn_off_techniques_obj).run()
        print(f"[Abaltion] {ablation_settings} done.\n")
        turn_off_techniques = [False, False, False, False] # to start the next iteration

if __name__ == "__main__":
    '''
    Run the following experiments on tracking annodated data A and B:
     * [off_diff] Disabling the diff-based candidate extraction
     * [off_move] Disabling the movement detection
     * [off_search] Disabling the text search
     * [off_fine] Disabling the refinement of candidate regions
     These 4 components can be optionally turned off, support turn off one or multiple at a time.
     * ! also consider [off_context] Disabling the context-aware similarity computation.
        [off_context] will be done in another ablation study (context size set to 0.)
    '''
    
    datasets = ["annotation_a", "annotation_b"] # the desired one or two annotated dataset(s)
    context_line_num = 15 
    turn_off_techniques = [False, False, False, False] 
    for dataset in datasets:
        oracle_file = join("data", "annotation", f"{dataset}.json")
        result_dir_parent = join("data", "results", "tracked_maps", dataset)
        time_file_folder = join("data", "results", "execution_time", dataset)
        makedirs(time_file_folder, exist_ok=True)  
        main_ablation_study(dataset, oracle_file, result_dir_parent, time_file_folder, context_line_num, turn_off_techniques)
