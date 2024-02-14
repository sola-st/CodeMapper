import argparse
import json
import os
from os.path import join
from anything_tracker.AnythingTracker import get_source_and_expected_region_characters
from anything_tracker.CandidateRegion import get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker.ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.baseline.git_line_level.LineLevelGitDiff import LineLevelGitDiff
from anything_tracker.utils.ReadFile import checkout_to_read_file

from multiprocessing import Pool
from anything_tracker.experiments.SourceRepos import SourceRepos
from anything_tracker.experiments.ComputeCandidatesForAnnoData import ComputeCandidatesForAnnoData


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--source_character_range", nargs='+', type=int, help="a 4-element list, to show where to track", required=True)
parser.add_argument("--results_dir", help="Directory to put the results", required=True)
parser.add_argument("--expected_character_range", nargs='+', 
                    type=int, help="a 4-element list, to show the expected character range", 
                    required=False) # only for the regions that with ground truth


class RunLineLevel():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_character_range, results_dir, expected_character_range=None):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.source_character_range = interest_character_range
        self.interest_character_range  = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
        self.results_dir = results_dir

        self.expected_character_range = expected_character_range
        if expected_character_range != None:
            self.expected_character_range = CharacterRange(expected_character_range)
            
        self.source_region_characters = []
        
    def write_regions_to_files(self, characters_to_write, is_source=True):
        json_file = join(self.results_dir, "source.json")
        to_write:str = ""

        if is_source == True: # source region
            to_write = {
                "source_file": self.file_path,
                "source_range": str(self.source_character_range),
                "source_characters": characters_to_write
            }
        else: # expected region
            expected_range = [0, 0, 0, 0]
            if  self.expected_character_range != None:
                expected_range = self.expected_character_range.four_element_list
                
            to_write = {
                "expected_file": self.file_path,
                "expected_range": str(expected_range),
                "expected_characters": characters_to_write
            }
            json_file = join(self.results_dir, "expect.json")

        # write region characters to a JSON file.
        with open(json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)


    def run(self):
        # create output folder
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        output_maps = []
        candidate_region = []

        # Read source region characters, write source character to json files. [Also for expected regions]
        self.base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.file_path)
        self.source_region_characters = get_source_and_expected_region_characters(self.base_file_lines, self.interest_character_range)
        source_region_characters_str = "".join(self.source_region_characters)
        self.write_regions_to_files(source_region_characters_str)

        expected_region_characters_str = "<DELETE>"
        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.file_path)
        if self.expected_character_range != None:
            expected_region_characters: list = get_source_and_expected_region_characters(self.target_file_lines, self.expected_character_range)
            expected_region_characters_str = "".join(expected_region_characters)

        self.write_regions_to_files(expected_region_characters_str, False)
        
        candidate_region = LineLevelGitDiff(self).run_git_diff()
       
        if candidate_region == []:
            print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")
            return
        
        for candidate in candidate_region:
            target_range = get_candidate_region_range(candidate)
            map = {
                "source_file": self.file_path,
                "target_file": self.file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "target_characters" : candidate.character_sources,
                "kind": candidate.marker,
                "index": 0, 
                "all_candidates_num": 1
            }
            output_maps.append(map)
        
        # write candidates to a JSON file. # also candidate.json
        candidate_json_file = join(self.results_dir, "target.json")
        with open(candidate_json_file, "w") as ds:
            json.dump(output_maps, ds, indent=4, ensure_ascii=False)


def wrapper(args):
    RunLineLevel(*args).run()
    source_region_index = args[-2].split('/')[-1]
    print(f"Compute candidates is done, source region #{source_region_index}.")

if __name__ == "__main__":
    result_dir_parent = join("data", "results", "tracked_maps", "candidate_regions_git_line_38_v2")
    oracle_file = join("data", "annotation", "anno_38.json")
    # is_reversed_data = False
    source_repo_init = SourceRepos()
    repo_dirs = source_repo_init.get_repo_dirs()
    source_repo_init.checkout_latest_commits()
    print(f"Found {len(repo_dirs)} repositories.")

    args_for_all_maps = ComputeCandidatesForAnnoData(oracle_file, result_dir_parent, False).get_meta_inputs()
    
    cores_to_use = 1
    with Pool(processes=cores_to_use) as pool:
        pool.map(wrapper, args_for_all_maps)