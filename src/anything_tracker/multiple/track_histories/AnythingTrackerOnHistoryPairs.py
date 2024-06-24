import argparse
import json
import os
from os.path import join
import time
from anything_tracker.AnythingTrackerUtils import (
    deduplicate_candidates,
    get_context_aware_characters,
    get_context_aware_unchanged_characters,
    get_source_and_expected_region_characters,
)
from anything_tracker.CandidateRegion import CandidateRegion, get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker. ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.GitDiffToCandidateRegion import GitDiffToCandidateRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion
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
parser.add_argument("--context_line_num", type=int, help="specify the line numbers of contexts", required=True) # 0 means no contexts
parser.add_argument("--turn_off_techniques", help="specify techniques to turn off", required=True)


class AnythingTrackerOnHistoryPairs():
    def __init__(self, repo_dir, base_commit, source_file_path, target_commit, target_file_path, interest_character_range, 
                results_dir, iteration_index, context_line_num, turn_off_techniques, expected_character_range=None):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.source_file_path = source_file_path
        self.target_commit = target_commit
        self.target_file_path = target_file_path
        self.source_character_range = interest_character_range
        self.interest_character_range = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
        self.results_dir = results_dir
        self.iteration_index = iteration_index
        self.context_line_num = context_line_num
        self.turn_off_techniques = turn_off_techniques # SpecifyToTurnOffTechniques object
        self.expected_character_range = expected_character_range
        if expected_character_range != None:
            self.expected_character_range = CharacterRange(expected_character_range)

        self.source_region_characters = []
        # return the following values
        self.dist_based_target_str_list = []

        # record execution time
        # "candidate_numbers", "compute_candidates_executing_time", "select_target_executing_time"
        self.one_round_time_info = [None]*3
        self.changed_line_numbers_version_maps_source = []
        self.changed_line_numbers_version_maps_target = []
        
    def write_regions_to_files(self, characters_to_write, is_source=True):
        json_file = join(self.results_dir, self.iteration_index, "source.json")
        to_write:str = ""

        if is_source == True: # source region
            to_write = {
                "source_file": self.source_file_path,
                "source_range": str(self.source_character_range),
                # "source_characters": characters_to_write
            }
        else: # expected region
            expected_range = [0, 0, 0, 0]
            if  self.expected_character_range != None:
                expected_range = self.expected_character_range.four_element_list
                
            to_write = {
                "expected_file": self.source_file_path,
                "expected_range": str(expected_range),
                # "expected_characters": characters_to_write
            }
            json_file = join(self.results_dir, self.iteration_index, "expect.json")

        # write region characters to a JSON file.
        with open(json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)

    def compute_candidate_regions(self):
        # phase 1: compute candidate regions.
        candidate_regions = []
        regions = []
        # get candidates from git diff
        diff_candidates, diff_hunk_lists, self.changed_line_numbers_version_maps_source, \
                self.changed_line_numbers_version_maps_target = GitDiffToCandidateRegion(self).run_git_diff()
        
        item_to_extend_source = self.changed_line_numbers_version_maps_source[0]
        item_to_extend_target = self.changed_line_numbers_version_maps_target[0]

        depulicated_diff_candidates = []
        if diff_candidates:
            depulicated_diff_candidates, regions, duplicated_indices = deduplicate_candidates(diff_candidates, regions)
            if depulicated_diff_candidates:
                candidate_regions.extend(depulicated_diff_candidates)
            # if the candidates is dupliacted, remove the pre-added changed_line_numbers
            for removed_count, idx in enumerate(duplicated_indices):
                pop_idx = len(diff_candidates) + idx - removed_count
                self.changed_line_numbers_version_maps_source.pop(pop_idx)
                self.changed_line_numbers_version_maps_target.pop(pop_idx)

        # search to map characters
        no_hunk_list = False
        if not diff_hunk_lists:
            # add an empty hunkj list to get searched candidate regions.
            no_hunk_list = True
            diff_hunk_lists.append(["Search-specific", [], [], []])
        for iter in diff_hunk_lists:
            search_candidates = []
            algorithm, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = iter
            search_candidates = SearchLinesToCandidateRegion(algorithm, self,
                    top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).search_maps()
            if search_candidates:
                depulicated_search_candidates, regions, duplicated_indices = deduplicate_candidates(search_candidates, regions)
                if depulicated_search_candidates:
                    candidate_regions.extend(depulicated_search_candidates)
                if no_hunk_list == False:
                    for removed_count, idx in enumerate(duplicated_indices):
                        pop_idx = len(depulicated_diff_candidates) + idx - removed_count
                        self.changed_line_numbers_version_maps_source.pop(pop_idx)
                        self.changed_line_numbers_version_maps_target.pop(pop_idx)
            # else: no overlapped hunks
        len_delta = len(candidate_regions) - len(self.changed_line_numbers_version_maps_source)
        if len_delta != 0:
            for i in range(len_delta):
                self.changed_line_numbers_version_maps_source.append(item_to_extend_source)
                self.changed_line_numbers_version_maps_target.append(item_to_extend_target)

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
        self.write_regions_to_files(source_region_characters_str)

        # write the candidates to json files
        self.record_candiates(candidate_regions)
        # phase 2: compute target region
        # accumulate target, write to json file later.
        self.compute_target_region_info(candidate_regions, source_region_characters_str)

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
                # "target_characters" : candidate.character_sources,
                "kind": candidate.marker
            }
            output_maps.append(map)

        # write candidates to a JSON file.
        candidate_json_file = join(self.results_dir, self.iteration_index, "candidates.json")
        with open(candidate_json_file, "w") as ds:
            json.dump(output_maps, ds, indent=4, ensure_ascii=False)

    def compute_target_region_info(self, candidate_regions, source_region_characters_str):
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
                "target_candidate_edit_distance": None,
                "target_candidate_index" : 0,
                "region_weight": None
                }})
        else:
            candiate_str_list = []
            source_str = source_region_characters_str
            source_str_list = [] # only for with context

            # collect candidate str, and contexts
            pre_changed_line_numbers = None
            source_with_context = ""
            for i, candidate in enumerate(candidate_regions):
                # option 1: without context
                if self.context_line_num == 0:
                    candidate_characters = candidate.character_sources
                    candiate_str_list.append(candidate_characters)
                else: # option 2: with context
                    # 2.1 check the characters with contexts at once
                    if pre_changed_line_numbers != self.changed_line_numbers_version_maps_source[i]:
                        source_with_context = get_context_aware_unchanged_characters(self.base_file_lines, self.interest_character_range, \
                                    self.context_line_num, self.context_line_num, self.changed_line_numbers_version_maps_source[i])
                    source_str_list.append(source_with_context)
                    candidate_range = candidate.candidate_region_character_range
                    candidate_with_context = get_context_aware_unchanged_characters(self.target_file_lines, candidate_range, \
                            self.context_line_num, self.context_line_num, self.changed_line_numbers_version_maps_target[i])
                    candiate_str_list.append(candidate_with_context)

            assert candiate_str_list != []
            if source_str_list:
                source_str = source_str_list
            results_set_dict = ComputeTargetRegion(source_str, candiate_str_list).run()
            second_phrase_end_time = time.time()
            second_phrase_executing_time = round((second_phrase_end_time - second_phrase_start_time), 3)
            print(f"Executing time (2nd phase): {second_phrase_executing_time} seconds")

        self.one_round_time_info[2] = second_phrase_executing_time

        for key, target_dict in results_set_dict.items():
            target_candidate = candidate_regions[target_dict["target_candidate_index"]]
            target_range: list = target_candidate.candidate_region_character_range.four_element_list
            if target_range.count(0) >= 3: # for diff deletions: [0, 0, target_hunk_range.stop, 0]
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
                # "source_characters": source_region_characters_str,
                # "target_characters" : target_candidate.character_sources,
                "kind": target_candidate.marker,
                "levenshtein_distance" : target_dict["target_candidate_edit_distance"],
                "index": target_dict["target_candidate_index"], 
                "all_candidates_num": len(candidate_regions),
                "region_weight": target_dict["region_weight"]
            }
            self.dist_based_target_str_list.append(target_json)


def main(*args):
    repo_dir, source_commit, source_file_path, target_commit, source_range, \
            results_dir, context_line_num, time_file_to_write, turn_off_techniques = args
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
            "all_candidates_num": 1,
            "region_weight": None
        }
        dist_based.append(target_json)
        candidate_numbers = 1
        print("No target file.")
    else:
        dist_based, one_round_time_info = AnythingTrackerOnHistoryPairs(repo_dir, source_commit, source_file_path,\
                target_commit, target_file_path, source_range, ground_truth_results_dir, current_history_pair_idx, \
                context_line_num, turn_off_techniques).run()
        candidate_numbers, times_1st, times_2nd = one_round_time_info

    # write exection times
    write_mode = "a"
    if ground_truth_index == "0" and current_history_pair_idx == "0":
        write_mode = "w"
    # current_history_pair_idx is used to control where to add an empty line
    RecordExecutionTimes(write_mode, time_file_to_write, ground_truth_index, \
            candidate_numbers, times_1st, times_2nd, current_history_pair_idx).run()
    
    return dist_based

def main_suppression(*args): # can be used to start tracking annotation and suppressions
    repo_dir, source_commit, source_file_path, target_commit, source_range, results_dir, \
            context_line_num, time_file_to_write, turn_off_techniques, ground_truth_index, write_mode = args
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
            "all_candidates_num": 1,
            "region_weight": None
        }
        dist_based.append(target_json)
        candidate_numbers = 1
        print("No target file.")
    else:
        dist_based, one_round_time_info = AnythingTrackerOnHistoryPairs(repo_dir, source_commit, source_file_path,\
                target_commit, target_file_path, source_range, results_dir, ground_truth_index, \
                context_line_num, turn_off_techniques).run()
        candidate_numbers, times_1st, times_2nd = one_round_time_info

    # write exection times
    RecordExecutionTimes(write_mode, time_file_to_write, ground_truth_index, candidate_numbers, times_1st, times_2nd).run()
    
    return dist_based
