import argparse
import csv
import json
import os
from os.path import join
import time
from anything_tracker.AnythingTrackerUtils import (
    deduplicate_candidates,
    get_context_aware_characters,
    get_renamed_file_path,
    get_source_and_expected_region_characters,
)
from anything_tracker.CandidateRegion import CandidateRegion, get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker. ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.GitDiffToCandidateRegion import GitDiffToCandidateRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion
from anything_tracker.collect.data_preprocessor.GetCommitsModifiedFile import check_modified_commits
from anything_tracker.collect.data_preprocessor.utils.UnifyKeys import UnifyKeys
from anything_tracker.multiple.on_converted_data.RecordComputeExecutionTimes import RecordComputeExecutionTimes
from anything_tracker.utils.ReadFile import checkout_to_read_file


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--source_character_range", nargs='+', type=int, help="a 4-element list, to show where to track", required=True)
parser.add_argument("--results_dir", help="Directory to put the results", required=True)
parser.add_argument("--iteration_index", type=str, help="the xxth round of tracking", required=True)
parser.add_argument("--context_line_num", type=int, help="specify the line numbers of contexts", required=True) # 0 means no contexts
parser.add_argument("--turn_off_techniques", help="specify techniques to turn off", required=True)
parser.add_argument("--expected_character_range", nargs='+', 
                    type=int, help="a 4-element list, to show the expected character range", 
                    required=False) # only for the regions that with ground truth


class AnythingTrackerOnConvertedData():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_character_range, 
                results_dir, iteration_index, context_line_num, turn_off_techniques, expected_character_range=None):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.source_character_range = interest_character_range
        self.interest_character_range  = character_range_init = CharacterRange(interest_character_range)
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
        self.unique_target_range = []
        self.accumulate_dist_based = []
        self.accumulate_bleu_based = []
        self.accumulate_similarity_based = []

        # record execution time
        # "candidate_numbers", "compute_candidates_executing_time", "select_target_executing_time"
        self.one_round_time_info = [None]*3
        
    def write_regions_to_files(self, characters_to_write, is_source=True):
        json_file = join(self.results_dir, self.iteration_index, "source.json")
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
            json_file = join(self.results_dir, self.iteration_index, "expect.json")

        # write region characters to a JSON file.
        with open(json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)

    def compute_candidate_regions(self):
        # phase 1: compute candidate regions.
        candidate_regions = []
        regions = []
        # get candidates from git diff
        diff_candidates, diff_hunk_lists = GitDiffToCandidateRegion(self).run_git_diff()
        if diff_candidates:
            depulicated_diff_candidates, regions = deduplicate_candidates(diff_candidates, regions) # True
            candidate_regions.extend(depulicated_diff_candidates)
        # search to map characters
        for iter in diff_hunk_lists:
            search_candidates = []
            algorithm, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks, may_moved = iter
            search_candidates = SearchLinesToCandidateRegion(algorithm, self,
                    top_diff_hunks, middle_diff_hunks, bottom_diff_hunks, may_moved).search_maps()
            if search_candidates:
                depulicated_search_candidates, regions = deduplicate_candidates(search_candidates, regions)
                candidate_regions.extend(depulicated_search_candidates)
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
        dir = join(self.results_dir, self.iteration_index)
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Read source region characters, and expected regions
        self.base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.file_path)
        self.source_region_characters = get_source_and_expected_region_characters(self.base_file_lines, self.interest_character_range)

        self.target_file_path = get_renamed_file_path(self.repo_dir, self.base_commit, self.target_commit, self.file_path)
        if not self.target_file_path:
            self.target_file_path = self.file_path
        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.target_file_path)

        candidate_regions = []
        if self.target_file_lines:
            # phase 1: compute candidate regions
            candidate_regions = self.compute_candidate_regions()
        else:
            # create an "null" candidate region
            candidate_region_character_range = CharacterRange([0, 0, 0, 0])
            target_characters = None
            marker = "no target file"
            null_region = CandidateRegion(self.source_character_range, candidate_region_character_range, target_characters, marker)
            candidate_regions.append(null_region)
            
        print(f"Iteration #{self.iteration_index}")
        first_phrase_end_time = time.time()
        first_phrase_executing_time = round((first_phrase_end_time - first_phrase_start_time), 3)
        self.one_round_time_info[1] = first_phrase_executing_time
        print(f"Executing time (1st phase): {first_phrase_executing_time} seconds")
        if candidate_regions == [] and self.target_file_lines:
            print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")
            return self.unique_target_range, self.accumulate_dist_based, self.accumulate_bleu_based, self.accumulate_similarity_based
        
        # write source character to json files
        source_region_characters_str = "".join(self.source_region_characters)
        self.write_regions_to_files(source_region_characters_str)

        # write the candidates to json files
        self.record_candiates(candidate_regions)
        # phase 2: compute target region
        # accumulate target, write to json file later.
        self.compute_get_target_region_info(candidate_regions, source_region_characters_str)

        self.one_round_time_info[0] = len(candidate_regions)
        return self.unique_target_range, self.accumulate_dist_based, self.accumulate_bleu_based, \
                self.accumulate_similarity_based, self.target_file_path, self.one_round_time_info
    
    def record_candiates(self, candidate_regions):
        output_maps = []

        # record candidates
        for candidate in candidate_regions:
            target_range = get_candidate_region_range(candidate)
            map = {
                "source_commit": self.base_commit,
                "target_commit": self.target_commit,
                "source_file": self.file_path,
                "target_file": self.target_file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "target_characters" : candidate.character_sources,
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
        # when decided, will focus on only 1 metric
        to_write = []
        results_set_dict = {}
        
        second_phrase_executing_time = 0
        if len(candidate_regions) == 1:
            # phase 2: compute candidate regions ends.
            print(f"Executing time (2nd phase): 1 candidate, {second_phrase_executing_time} seconds")
            target_candidate = candidate_regions[0]
            unique_keys = ["dist_based", "bleu_based", "similarity_based"]
            for key in unique_keys:
                results_set_dict.update({key: { 
                    "idx": 0,
                    "target_candidate_edit_distance": "Unknown",
                    "target_candidate_bleu_score": "Unknown",
                    "target_candidate_similarity": "Unknown",
                    "target_candidate_index" : 0
                    }})
        else:
            candiate_str_list = []
            source_str = ""
            # option 1: without context
            if self.context_line_num == 0:
                source_str = source_region_characters_str
                for candidate in candidate_regions:
                    candidate_characters = candidate.character_sources
                    candiate_str_list.append(candidate_characters)
            else: # option 2: with context
            #     # 2.1 check the characters with contexts ar once
            #     before_lines_num = self.context_line_num
            #     after_line_num = self.context_line_num
            #     source_str = get_context_aware_characters(self.base_file_lines, self.interest_character_range, before_lines_num, after_line_num)
            #     for candidate in candidate_regions:
            #         candidate_range = candidate.candidate_region_character_range
            #         candidate_with_context = get_context_aware_characters(self.target_file_lines, candidate_range, before_lines_num, after_line_num)
            #         candiate_str_list.append(candidate_with_context)
            # results_set_dict, average_highest, vote_most = ComputeTargetRegion(source_str, candiate_str_list).run()
                
                # 2.2 check pre, post separately
                source_str = source_region_characters_str
                before_lines_num = self.context_line_num
                after_line_num = self.context_line_num
                source_pre_lines_str, source_post_lines_str = get_context_aware_characters(self.base_file_lines, \
                            self.interest_character_range, before_lines_num, after_line_num)
                for candidate in candidate_regions:
                    candidate_range = candidate.candidate_region_character_range
                    # candidate_with_context 
                    candidate_pre_lines_str, candidate_post_lines_str = get_context_aware_characters(self.target_file_lines, \
                            candidate_range, before_lines_num, after_line_num)
                    candidate_str = candidate.character_sources
                    candiate_str_list.append([candidate_pre_lines_str, candidate_str, candidate_post_lines_str])
            # special for 2.2
            # results_set_dict, average_highest, vote_most = ComputeTargetRegionWithContext(\
            #         [source_pre_lines_str, source_str, source_post_lines_str], candiate_str_list).run()
                    
            # for both 1 and 2.1
            results_set_dict = ComputeTargetRegion(source_str, candiate_str_list).run()

            # phase 2: compute candidate regions ends.
            second_phrase_end_time = time.time()
            second_phrase_executing_time = round((second_phrase_end_time - second_phrase_start_time), 3)
            print(f"Executing time (2nd phase): {second_phrase_executing_time} seconds")

        self.one_round_time_info[2] = second_phrase_executing_time

        for key, target_dict in results_set_dict.items():
            target_candidate = candidate_regions[target_dict["idx"]]
            target_range: list = target_candidate.candidate_region_character_range.four_element_list
            target_json = {
                "iteration": self.iteration_index,
                "version" : key,
                "source_commit": self.base_commit,
                "target_commit": self.target_commit,
                "source_file": self.file_path,
                "target_file": self.file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "source_characters": source_region_characters_str,
                "target_characters" : target_candidate.character_sources,
                "kind": target_candidate.marker,
                "levenshtein_distance" : target_dict["target_candidate_edit_distance"],
                "bleu": target_dict["target_candidate_bleu_score"],
                "embedding_similarity" : str(target_dict["target_candidate_similarity"]),
                "index": target_dict["target_candidate_index"], 
                "all_candidates_num": len(candidate_regions)
            }
            to_write.append(target_json)
            if key == "dist_based":
                if target_candidate.character_sources != None:
                    if target_candidate.character_sources.strip(): 
                        # case like "  \n", delelte the source, and add an empty line.
                        self.unique_target_range = target_range
                    else:
                        self.unique_target_range = [0, 0, 0, 0] 
                else:
                    self.unique_target_range = [0, 0, 0, 0] 
                self.accumulate_dist_based.append(target_json)
            elif key == "bleu_based":
                self.accumulate_bleu_based.append(target_json)
            else:
                self.accumulate_similarity_based.append(target_json)


def main(*args):
    repo_dir, base_commit, category, source_info, file_path, interest_character_range, \
            results_dir, context_line_num, time_file_to_write, turn_off_techniques = args
    # commits_to_track includes source commit and target commit.
    addtional_info = None
    key_init = UnifyKeys()
    partial_categoris = key_init.partial_categoris
    
    if category in partial_categoris or category == "block":
        start = interest_character_range[0]
        end = interest_character_range[-1]
        addtional_info = f"{start},{end}"

    commits_to_track = check_modified_commits(repo_dir, base_commit, file_path, category, addtional_info)
    print(commits_to_track)
    if base_commit != commits_to_track[0]:
        assert base_commit not in commits_to_track
        commits_to_track.insert(0, base_commit)

    source_commits = commits_to_track[:-1]
    target_commits = commits_to_track[1:]
    iterations = range(len(source_commits))

    # metrics and target regions
    accumulate_dist_based = []
    accumulate_bleu_based = []
    accumulate_similarity_based = []

    # execution times
    indices = []
    ground_truth_index = results_dir.rsplit("/", 1)[1]
    indices.append(ground_truth_index)
    candi_nums = [] 
    times_1st = [] 
    times_2nd = []

    source_range = interest_character_range
    for i, s, t in zip(iterations, source_commits, target_commits):
        middle_target_range, dist_based, bleu_based, similarity_based, renamed_file_path, one_round_time_info = \
                AnythingTrackerOnConvertedData(repo_dir, s, t, file_path, source_range, results_dir, \
                str(i), context_line_num, turn_off_techniques).run()
        
        accumulate_dist_based.extend(dist_based)
        accumulate_bleu_based.extend(bleu_based)
        accumulate_similarity_based.extend(similarity_based)

        indices.append(None)
        candi_nums.append(one_round_time_info[0])
        times_1st.append(one_round_time_info[1])
        times_2nd.append(one_round_time_info[2])

        if middle_target_range == [0, 0, 0, 0]:
            break
        source_range = middle_target_range
        file_path = renamed_file_path

    # write target candidate to a Json file.   
    to_write = [accumulate_dist_based, accumulate_bleu_based, accumulate_similarity_based]
    target_json_file = join(results_dir, "target.json")
    with open(target_json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)

    # write exection times
    write_mode = "a"
    if ground_truth_index == "0":
        write_mode = "w"
    RecordComputeExecutionTimes(write_mode, time_file_to_write, indices, candi_nums, times_1st, times_2nd).run()
