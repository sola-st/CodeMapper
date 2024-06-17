import json
from anything_tracker.AnythingTrackerUtils import get_source_and_expected_region_characters
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.experiments.SourceRepos import SourceRepos
from os.path import join
from os import makedirs
from anything_tracker.utils.ReadFile import checkout_to_read_file


class ComputeCandidatesForAnnoData():
    """
    Computes candidate region for all the source regions.
    """
    def __init__(self, oracle_file, result_file):
        self.oracle_file = oracle_file
        self.result_file = result_file
        
    def get_region_zises(self):
        region_size_recorder = []

        with open(self.oracle_file) as f:
            maps = json.load(f)

        for i, meta in enumerate(maps):
            url = meta["url"]
            tmp = url.split("/")
            repo_name = tmp[-1]
            repo_dir = join("data", "repos", repo_name)
            mapping:dict = meta["mapping"]
            source_file = mapping["source_file"]
            source_commit = mapping["source_commit"]
            character_range_list = json.loads(mapping["source_range"])
            file_lines = checkout_to_read_file(repo_dir, source_commit, source_file)
            interest_character_range = CharacterRange(character_range_list)
            source_region_characters = get_source_and_expected_region_characters(file_lines, interest_character_range)
            size_ste = {
                "ground_truth_idx": i,
                "source_characters" : source_region_characters,
                "region_size": len("".join(source_region_characters))
            }
            region_size_recorder.append(size_ste)

        self.write_target_regions(region_size_recorder)

    def run(self):
        # prepare repositories
        source_repo_init = SourceRepos()
        repo_dirs = source_repo_init.get_repo_dirs()
        source_repo_init.checkout_latest_commits()
        print(f"Found {len(repo_dirs)} repositories.")
        self.get_region_zises()

    def write_target_regions(self, to_write):
        target_json_file = join(self.result_file)
        with open(target_json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    oracle_file = join("data", "annotation", "annotations_100.json")
    results_file_folder = join("data", "results", "table_plots")
    makedirs(results_file_folder, exist_ok=True)
    result_file = join(results_file_folder, "region_size_meta_anno.json")
    ComputeCandidatesForAnnoData(oracle_file, result_file).run()