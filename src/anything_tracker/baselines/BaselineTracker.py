import argparse
import json
import os
from os.path import join
import time
from anything_tracker.AnythingTrackerUtils import (
    deduplicate_candidates,
    get_source_and_expected_region_characters,
)
from anything_tracker.CandidateRegion import CandidateRegion, get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker. ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.baselines.CombineToCandidateRegion import CombineToCandidateRegion
from anything_tracker.baselines.LineCharacterGitDiffToCandidateRegion import LineCharacterGitDiffToCandidateRegion
from anything_tracker.multiple.GetTargetFilePath import get_target_file_path
from anything_tracker.multiple.track_histories.RecordExecutionTimes import RecordExecutionTimes
from anything_tracker.utils.ReadFile import checkout_to_read_file


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--source_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--source_file_path", help="the source file that you want to track", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--target_file_path", help="the target file that you want to track", required=True)
parser.add_argument("--source_character_range", nargs='+', type=int, help="a 4-element list, to show where to track", required=True)
parser.add_argument("--results_dir", help="Directory to put the results", required=True)
parser.add_argument("--iteration_index", type=str, help="the xxth round of tracking", required=True)


class BaselineTracker():
    def __init__(self, level, repo_dir, base_commit, source_file_path, target_commit, target_file_path, interest_character_range, 
                results_dir, iteration_index):
        self.level = level
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.source_file_path = source_file_path
        self.target_commit = target_commit
        self.target_file_path = target_file_path
        self.source_character_range = interest_character_range
        self.interest_character_range  = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
        self.results_dir = results_dir
        self.iteration_index = iteration_index

        self.source_region_characters = []
        # return the following values
        self.dist_based_target_str_list = []

        # record execution time
        # "candidate_numbers", "compute_candidates_executing_time", "select_target_executing_time"
        self.one_round_time_info = [None]*3
        
    def write_regions_to_files(self):
        json_file = join(self.results_dir, self.iteration_index, "source.json")
        to_write:str = ""

        to_write = {
            "source_file": self.source_file_path,
            "source_range": str(self.source_character_range),
        }

        # write region characters to a JSON file.
        with open(json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)

    def compute_candidate_regions(self):
        # phase 1: compute candidate regions.
        candidate_regions = []
        regions = []
        # get candidates from git diff
        diff_candidates, diff_hunk_lists = LineCharacterGitDiffToCandidateRegion(self).run_git_diff()
        if diff_candidates:
            depulicated_diff_candidates, regions = deduplicate_candidates(diff_candidates, regions) # True
            candidate_regions.extend(depulicated_diff_candidates)
        # search to map characters
        for iter in diff_hunk_lists:
            algorithm, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = iter
            combined_candidates = CombineToCandidateRegion(algorithm, self,
                    top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).search_maps()
            if combined_candidates:
                depulicated_candidates, regions = deduplicate_candidates(combined_candidates, regions)
                candidate_regions.extend(depulicated_candidates)
        return candidate_regions

    def run(self):
        ''' 
        Step 1: Get all candidate candidates
        * 1.1 git diff changed hunks
        * 1.2 exactly mapped characters
        * 1.3 ...
        '''
       
        first_phrase_start_time = time.time()
        # create output folder
        os.makedirs(join(self.results_dir, self.iteration_index), exist_ok=True)

        # Read source region characters, and expected regions
        self.base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.source_file_path)
        self.source_region_characters = get_source_and_expected_region_characters(self.base_file_lines, self.interest_character_range)

        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.target_file_path)

        # phase 1: compute candidate regions
        candidate_regions = self.compute_candidate_regions()
        print(f"Iteration #{self.iteration_index}")
        first_phrase_end_time = time.time()
        first_phrase_executing_time = round((first_phrase_end_time - first_phrase_start_time), 3)
        self.one_round_time_info[1] = first_phrase_executing_time
        print(f"Executing time (1st phase): {first_phrase_executing_time} seconds")
        if candidate_regions == [] and self.target_file_lines:
            print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.source_file_path}\n  {self.interest_character_range.four_element_list}\n")
            self.one_round_time_info[2] = 0
            # return self.dist_based_target_str_list, self.one_round_time_info
            # create an "null" candidate region
            candidate_region_character_range = CharacterRange([0, 0, 0, 0])
            target_characters = None
            marker = "no candidate regions"
            null_region = CandidateRegion(self.source_character_range, candidate_region_character_range, target_characters, marker)
            candidate_regions.append(null_region)
        
        # write source character to json files
        source_region_characters_str = "".join(self.source_region_characters)

        # write the candidates to json files
        self.record_candiates(candidate_regions)
        # phase 2: compute target region
        # accumulate target, write to json file later.
        self.compute_get_target_region_info(candidate_regions, source_region_characters_str)

        self.one_round_time_info[0] = len(candidate_regions)
        return self.dist_based_target_str_list, self.one_round_time_info
    
    def record_candiates(self, candidate_regions):
        output_maps = []

        # record candidates
        for candidate in candidate_regions:
            target_range = get_candidate_region_range(candidate)
            map = {
                "source_commit": self.base_commit,
                "target_commit": self.target_commit,
                "source_file": self.source_file_path,
                "target_file": self.target_file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "kind": candidate.marker
            }
            output_maps.append(map)

        # write candidates to a JSON file.
        candidate_json_file = join(self.results_dir, self.iteration_index, "candidates.json")
        with open(candidate_json_file, "w") as ds:
            json.dump(output_maps, ds, indent=4, ensure_ascii=False)

    def compute_get_target_region_info(self, candidate_regions, source_region_characters_str):
        # phase 2: compute candidate regions starts.
        second_phrase_start_time = time.time()
        # -- Select top-1 candidate from multiple candidates
        results_set_dict = {}
        
        second_phrase_executing_time = 0
        if len(candidate_regions) == 1:
            # phase 2: compute candidate regions ends.
            print(f"Executing time (2nd phase): 1 candidate, {second_phrase_executing_time} seconds")
            target_candidate = candidate_regions[0]
            results_set_dict.update({"dist_based": { 
                "target_candidate_edit_distance": "Unknown",
                "target_candidate_index" : 0
                }})
        else:
            candiate_str_list = []
            source_str = ""

            for candidate in candidate_regions:
                # without context
                source_str = source_region_characters_str
                candidate_characters = candidate.character_sources
                candiate_str_list.append(candidate_characters)
                    
            assert candiate_str_list != []
            if len(candiate_str_list) > 1:
                results_set_dict = ComputeTargetRegion(source_str, candiate_str_list).run()
                # phase 2: compute candidate regions ends.
                second_phrase_end_time = time.time()
                second_phrase_executing_time = round((second_phrase_end_time - second_phrase_start_time), 3)
                print(f"Executing time (2nd phase): {second_phrase_executing_time} seconds")
            else: # == 1
                second_phrase_end_time = time.time()
                second_phrase_executing_time = round((second_phrase_end_time - second_phrase_start_time), 3)
                print(f"Executing time (2nd phase): line deduplicate, 1 candidate, {second_phrase_executing_time} seconds")
                idx = 0
                target_candidate = candidate_regions[idx]
                results_set_dict.update({"dist_based": { 
                    "target_candidate_edit_distance": "Unknown",
                    "target_candidate_index" : idx
                }})

        self.one_round_time_info[2] = second_phrase_executing_time

        for key, target_dict in results_set_dict.items():
            target_candidate = candidate_regions[target_dict["target_candidate_index"]]
            target_range: list = target_candidate.candidate_region_character_range.four_element_list
            if target_range == [0, 0, 0, 0]:
                target_range = None
            else:
                target_range = str(target_range)

            target_json = {
                "iteration": self.iteration_index,
                "version" : key,
                "source_commit": self.base_commit,
                "target_commit": self.target_commit,
                "source_file": self.source_file_path,
                "target_file": self.target_file_path,
                "source_range": str(self.source_character_range),
                "target_range": target_range,
                "kind": target_candidate.marker,
                "levenshtein_distance" : target_dict["target_candidate_edit_distance"],
                "index": target_dict["target_candidate_index"], 
                "all_candidates_num": len(candidate_regions)
            }
            self.dist_based_target_str_list.append(target_json)


def main(*args):
    level, repo_dir, source_commit, source_file_path, target_commit, source_range, \
            results_dir, time_file_to_write = args
    dist_based = []
    candidate_numbers = 0
    times_1st = 0
    times_2nd = 0
    tmp = results_dir.split("/")
    ground_truth_index = tmp[-2] # eg., method/test/15 # the number 16(abs) data in method/test
    current_history_pair_idx = tmp[-1] # eg., method/test/15/0, the 1st history pair in 15.
    ground_truth_results_dir = results_dir.rsplit("/", 1)[0]

    # get target file path
    target_file_path = get_target_file_path(repo_dir, source_commit, target_commit, source_file_path)
    if isinstance(target_file_path, bool):
        # the file was deleted
        target_json = {
            "iteration": current_history_pair_idx,
            "version" : "dist_based",
            "source_commit": source_commit,
            "target_commit": target_commit,
            "source_file": source_file_path,
            "target_file": None,
            "source_range": str(source_range),
            "target_range": None,
            "kind": "no target file (deleted)",
            "levenshtein_distance" : None,
            "index": 0, 
            "all_candidates_num": 1
        }
        dist_based.append(target_json)
        candidate_numbers = 1
        print("No target file.")
    else:
        dist_based, one_round_time_info = BaselineTracker(level, repo_dir, source_commit, source_file_path,\
                target_commit, target_file_path, source_range, ground_truth_results_dir, current_history_pair_idx).run()
        candidate_numbers, times_1st, times_2nd = one_round_time_info

    # write exection times
    write_mode = "a"
    if ground_truth_index == "0" and current_history_pair_idx == "0":
        write_mode = "w"
    # current_history_pair_idx is used to control where to add an empty line
    RecordExecutionTimes(write_mode, time_file_to_write, ground_truth_index, \
            candidate_numbers, times_1st, times_2nd, current_history_pair_idx).run()
    
    return dist_based

def main_suppression_annodata(*args): # can be used to start tracking annotation and suppressions
    level, repo_dir, source_commit, source_file_path, target_commit, source_range, results_dir, \
            time_file_to_write, ground_truth_index, write_mode = args
    dist_based = []
    candidate_numbers = 0
    times_1st = 0
    times_2nd = 0
    # get target file path
    target_file_path = get_target_file_path(repo_dir, source_commit, target_commit, source_file_path)
    if isinstance(target_file_path, bool):
        # the file was deleted
        target_json = {
            "iteration": ground_truth_index,
            "version" : "dist_based",
            "source_commit": source_commit,
            "target_commit": target_commit,
            "source_file": source_file_path,
            "target_file": None,
            "source_range": str(source_range),
            "target_range": None,
            "kind": "no target file (deleted)",
            "levenshtein_distance" : None,
            "index": 0, 
            "all_candidates_num": 1
        }
        dist_based.append(target_json)
        candidate_numbers = 1
        print("No target file.")
    else:
        dist_based, one_round_time_info = BaselineTracker(level, repo_dir, source_commit, source_file_path,\
                target_commit, target_file_path, source_range, results_dir, ground_truth_index).run()
        candidate_numbers, times_1st, times_2nd = one_round_time_info

    # write exection times
    RecordExecutionTimes(write_mode, time_file_to_write, ground_truth_index, candidate_numbers, times_1st, times_2nd).run()
    
    return dist_based
