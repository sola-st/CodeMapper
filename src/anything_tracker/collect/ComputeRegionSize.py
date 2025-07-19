import csv
import json
import os
from anything_tracker.AnythingTrackerUtils import get_source_and_expected_region_characters
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs
from anything_tracker.utils.ReadFile import checkout_to_read_file


def compute_list_avg(value_list):
    return sum(value_list) / len(value_list)


class ComputeRegionSize():
    def __init__(self, oracle_file, results_file_folder, dataset):
        self.oracle_file = oracle_file
        self.results_file_folder = results_file_folder
        self.dataset = dataset 

        self.region_size_recorder = []
        self.overall_source_size = []
        self.overall_target_size = []
        self.overall_commit_distance = []
        
    def get_region_sizes_anno_tracker_data(self, repo_folder):
        with open(self.oracle_file) as f:
            maps = json.load(f)

        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1]
            repo_dir = join(repo_folder, repo_name)
            mapping:dict = meta["mapping"]
            # source
            source_region_size = 0
            source_file = mapping["source_file"]
            source_commit = mapping["source_commit"]
            character_range_list = json.loads(mapping["source_range"])
            file_lines = checkout_to_read_file(repo_dir, source_commit, source_file)
            if file_lines:
                interest_character_range = CharacterRange(character_range_list)
                source_region_characters = get_source_and_expected_region_characters(file_lines, interest_character_range)
                source_region_size = len("".join(source_region_characters))

            # target
            target_region_characters = None
            target_region_size = 0 
            if mapping["target_range"] != None:
                target_file = mapping["target_file"]
                target_commit = mapping["target_commit"]
                targte_character_range_list = json.loads(mapping["target_range"])
                target_file_lines = checkout_to_read_file(repo_dir, target_commit, target_file)
                if target_file_lines:
                    target_character_range = CharacterRange(targte_character_range_list)
                    target_region_characters = get_source_and_expected_region_characters(target_file_lines, target_character_range)
                    target_region_size = len("".join(target_region_characters))

            # commit siatance
            commit_distance = mapping["kind"]
            if commit_distance == "neighboring":
                commit_distance = 1
            else:
                commit_distance = int(commit_distance.replace("distance: ", ""))
            assert isinstance(commit_distance, int)

            # computation
            self.record_values(i, source_region_characters, source_region_size, \
                target_region_characters, target_region_size, commit_distance)
            
        self.write_json_strings()
        self.compute_and_write_sizes()
            
    def get_region_sizes_suppression(self, repo_dirs):
        for repo_dir in repo_dirs:
            repo_name = repo_dir.rsplit("/", 1)[1]
            oracle_folder = join(self.oracle_file, repo_name)
            oracle_num = len(os.listdir(oracle_folder))

            source_region_characters = None
            source_region_size = None
            for i in range(oracle_num):
                history_file = join(oracle_folder, str(i), "expect_full_histories.json")
                with open(history_file, "r") as f:
                    data = json.load(f)

                for his_idx, history_event in enumerate(data):
                    if his_idx == 0: # source, add event
                        source_file = history_event["file_path"]
                        source_commit = history_event["commit"]
                        character_range_list = json.loads(history_event["range"])
                        file_lines = checkout_to_read_file(repo_dir, source_commit, source_file)
                        interest_character_range = CharacterRange(character_range_list)
                        source_region_characters = get_source_and_expected_region_characters(file_lines, interest_character_range)
                        source_region_size = len("".join(source_region_characters))
                    else:
                        target_region_characters = None
                        target_region_size = 0 
                        target_file = history_event["file_path"]
                        target_commit = history_event["commit"]
                        if history_event["range"] != None:
                            targte_character_range_list = json.loads(history_event["range"])
                            target_file_lines = checkout_to_read_file(repo_dir, target_commit, target_file)
                            target_character_range = CharacterRange(targte_character_range_list)
                            target_region_characters = get_source_and_expected_region_characters(target_file_lines, target_character_range)
                            target_region_size = len("".join(target_region_characters))

                        # computation
                        self.record_values(f"{repo_name}_{i}", source_region_characters, source_region_size, \
                            target_region_characters, target_region_size) 
                        source_region_characters = None
                        source_region_size = None

        self.write_json_strings()
        self.compute_and_write_sizes()

    # common functions for both datasets, start
    def record_values(self, i, source_region_characters, source_region_size, \
                target_region_characters, target_region_size, commit_distance=None):
        self.overall_source_size.append(source_region_size)
        self.overall_target_size.append(target_region_size)
        self.overall_commit_distance.append(commit_distance)

        size_dict = {
            "ground_truth_idx": i,
            "source_characters" : source_region_characters,
            "source_region_size": source_region_size,
            "target_characters" : target_region_characters,
            "target_region_size": target_region_size,
            "commit_distance": commit_distance
        }
        self.region_size_recorder.append(size_dict)

    def compute_and_write_sizes(self):
        # compute the average values
        avg_source_size = compute_list_avg(self.overall_source_size)
        avg_target_size = compute_list_avg(self.overall_target_size)
        self.overall_source_size.append(avg_source_size)
        self.overall_target_size.append(avg_target_size)

        if self.dataset != "suppression":
            avg_commit_distance = compute_list_avg(self.overall_commit_distance)
            self.overall_commit_distance.append(avg_commit_distance)
        self.write_sizes()

    def write_json_strings(self):
        result_file = join(self.results_file_folder, f"region_size_meta_{self.dataset}.json")
        with open(result_file, "w") as ds:
            json.dump(self.region_size_recorder, ds, indent=4, ensure_ascii=False)

    def write_sizes(self):
        result_file = join(self.results_file_folder, f"region_size_dist_{self.dataset}.csv")
        zipped_sizes = zip(self.overall_source_size, self.overall_target_size, self.overall_commit_distance)
        with open(result_file, "w") as f:
            csv_writer = csv.writer(f)
            for size in zipped_sizes:
                csv_writer.writerow(list(size))
    # common functions end.

    def run(self):
        if dataset == "suppression":
            repo_urls_file = join("data", "python_repos.txt") # python projects
            repo_folder_suppression = join("data", "repos_suppression")
            source_repo_init = SourceRepos(repo_urls_file, repo_folder_suppression)
            repo_dirs = source_repo_init.get_repo_dirs()
            source_repo_init.checkout_latest_commits()
            print(f"Found {len(repo_dirs)} repositories.")
            self.get_region_sizes_suppression(repo_dirs)
        elif self.dataset in ["annotaion_a", "annotaion_b"]:
            # prepare repositories
            source_repo_init = SourceRepos()
            repo_dirs = source_repo_init.get_repo_dirs()
            source_repo_init.checkout_latest_commits()
            print(f"Found {len(repo_dirs)} repositories.")
            self.get_region_sizes_anno_tracker_data(join("data", "repos"))
        else:
            repo_urls_file = join("data", "source_repos_java.txt")
            repo_folder = join("data", "repos_tracker")
            source_repo_init = SourceRepos(repo_urls_file, repo_folder)
            repo_dirs = source_repo_init.get_repo_dirs()
            source_repo_init.checkout_latest_commits()
            print(f"Found {len(repo_dirs)} repositories.")
            self.get_region_sizes_anno_tracker_data(repo_folder)



if __name__ == "__main__":
    datasets = ["annotation_a", "annotation_b", "suppression", "variable", "block_test", "method_test"]
    results_file_folder = join("data", "results", "table_plots")
    makedirs(results_file_folder, exist_ok=True)

    for dataset in datasets:
        oracle_file = None
        if dataset == "suppression":
            oracle_file = join("data", "suppression_data") # it is a folder
        else:
            oracle_file = join("data", "annotation", f"{dataset}.json")
            
        ComputeRegionSize(oracle_file, results_file_folder, dataset).run()