import json
from anything_tracker.baselines.BaselineTracker import main_suppression_annodata as AnythingTracker
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs


class BaselineOnAnnoData():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_file, result_dir_parent, time_file_to_write, level):
        self.oracle_file = oracle_file
        self.result_dir_parent = result_dir_parent
        self.time_file_to_write = time_file_to_write
        self.level = level
        
    def get_meta_inputs(self):
        """
        Returns a list of parameter list.
        Each inner list contains repo_dir, base_commit, target_commit, file_path, and interest_character_range.
        """
        parameters = []

        with open(self.oracle_file) as f:
            maps = json.load(f)

        write_mode = "w" # for writing execution times
        # get inputs for computing candidates
        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            result_dir = join(self.result_dir_parent)

            mapping:dict = meta["mapping"]
            character_range_list = json.loads(mapping["source_range"])
            if i != 0:
                write_mode = "a"

            parameter = [
                self.level,
                repo_dir,
                mapping["source_commit"],
                mapping["source_file"],
                mapping["target_commit"],
                character_range_list,
                result_dir,
                self.time_file_to_write,
                str(i),
                write_mode
            ]
            parameters.append(parameter)

        return parameters

    def run(self):
        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")

        args_for_all_maps = self.get_meta_inputs()
        for args in args_for_all_maps:
            target_regions_for_1_data = AnythingTracker(*args)
            source_region_index = args[-2]
            print(f"Compute candidates is done, source region #{source_region_index}.\n")
            result_dir_with_num = join(args[6], source_region_index)
            self.write_target_regions(result_dir_with_num, target_regions_for_1_data)

    def write_target_regions(self, result_dir, target_regions_for_1_data):
        # write target candidate to a Json file.  
        makedirs(result_dir, exist_ok=True) 
        target_json_file = join(result_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(target_regions_for_1_data, ds, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    '''
    Run the following experiments on baselines:
     * line-level tracking on annotated data A
     * word-level tracking on annotated data A
     * line-level tracking on annotated data B
     * word-level tracking on annotated data B
    '''
    datasets = ["annotation_a", "annotation_b"]
    levels = ["line", "word"]
    for dataset in datasets:
        for level in levels:
            result_dir_parent = join("data", "results", "tracked_maps", dataset, f"mapped_regions_{dataset}_{level}")
            oracle_file = join("data", "annotation", f"{dataset}_100.json")
            time_file_folder = join("data", "results", "execution_time", dataset)
            makedirs(time_file_folder, exist_ok=True)
            time_file_to_write = join(time_file_folder, f"execution_time_{dataset}_{level}.csv")
            BaselineOnAnnoData(oracle_file, result_dir_parent, time_file_to_write, level).run()
            print(f"Baseline {level} level done for {dataset}.")