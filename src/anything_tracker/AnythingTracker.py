import argparse
import csv
import json
import os
from os.path import join
import time
from anything_tracker.CandidateRegion import get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
from anything_tracker. ComputeTargetRegion import ComputeTargetRegion
from anything_tracker.ComputeTargetRegionWithContext import ComputeTargetRegion as ComputeTargetRegionWithContext
from anything_tracker.GitDiffToCandidateRegion import GitDiffToCandidateRegion
from anything_tracker.SearchLinesToCandidateRegion import SearchLinesToCandidateRegion
from anything_tracker.utils.ReadFile import checkout_to_read_file


parser = argparse.ArgumentParser(description="Track anything you want between two different versions.")
parser.add_argument("--repo_dir", help="Directory with the repository to check", required=True)
parser.add_argument("--base_commit", help="the commit to get the 1st version of the target file", required=True)
parser.add_argument("--target_commit", help="the commit to get the 2nd version of the target file", required=True)
parser.add_argument("--file_path", help="the target file that you want to track", required=True)
parser.add_argument("--source_character_range", nargs='+', type=int, help="a 4-element list, to show where to track", required=True)
parser.add_argument("--results_dir", help="Directory to put the results", required=True)
parser.add_argument("--context_line_num", type=int, help="specify the line numbers of contexts", required=True) # 0 means no contexts
parser.add_argument("--time_file_to_write", help="the file you want to write the exexcuting times", required=True)
parser.add_argument("--turn_off_techniques", help="specify techniques to turn off", required=True)
parser.add_argument("--expected_character_range", nargs='+', 
                    type=int, help="a 4-element list, to show the expected character range", 
                    required=False) # only for the regions that with ground truth

def deduplicate_candidates(candidates, regions, reorder=False):
    deduplicated_candidates = []
    for s in candidates:
        r = s.candidate_region_character_range.four_element_list
        marker = s.marker
        if regions == []:
            regions.append(r)
            deduplicated_candidates.append(s)
        else:
            if r not in regions:
                if reorder == True and marker.startswith("<A>"):
                    # keep the one from anythingtracker core idea work, especially for single words.
                    regions.insert(0, r)
                    deduplicated_candidates.insert(0, s)
                else:
                    regions.append(r)
                    deduplicated_candidates.append(s)
    return deduplicated_candidates, regions

def get_context_aware_characters(file_lines, character_range, before_lines, after_lines):
    # character_range: start_line, start_character, end_line, end_character
    max_idx = len(file_lines)
    start_line_idx = character_range.start_line_idx
    end_line_idx = character_range.end_line_idx

    expected_start_idx = start_line_idx - before_lines - 1 # starts at 0
    if expected_start_idx < 0:
        expected_start_idx = 0

    expected_end = end_line_idx + after_lines
    if expected_end > max_idx:
        expected_end = max_idx

    # character_list = file_lines[expected_start_idx: expected_end]
    # characters = "".join(character_list)
    # return characters

    pre_lines_list = file_lines[expected_start_idx: start_line_idx]
    pre_lines_str = "".join(pre_lines_list)
    post_lines_list = file_lines[end_line_idx: expected_end]
    post_lines_str = "".join(post_lines_list)
    return pre_lines_str, post_lines_str


def get_source_and_expected_region_characters(file_lines, character_range):
    '''
    Initially get source_region_characters and expected region characters.
    '''
    characters = []

    # character_range: start_line, start_character, end_line, end_character
    start_line_idx = character_range.start_line_idx
    characters_start_idx = character_range.characters_start_idx
    end_line_idx = character_range.end_line_idx
    characters_end_idx = character_range.characters_end_idx

    start_line = str(file_lines[start_line_idx-1])

    if start_line_idx == end_line_idx: 
        # the source or expected region is inside one line.
        # only records one line number, that is, the start and end are on the same line.
        characters.append(start_line[characters_start_idx-1 : characters_end_idx])
    else:
        # covers multi-line
        # separate to 3 sections: start line, middle lines, and end line.
        # section 1: start line : the entire line is covered
        characters_in_start_line = start_line[characters_start_idx-1:] 
    
        # section 2: middle lines : all covered
        characters_in_middle_lines= []
        if start_line_idx + 1 != end_line_idx:
            characters_in_middle_lines = file_lines[start_line_idx : end_line_idx - 1]

        # section 3: end line : [character index [0: specified_index]]
        end_line = str(file_lines[end_line_idx-1]) 
        characters_in_end_line = end_line[:characters_end_idx]

        characters.append(characters_in_start_line) 
        characters.extend(characters_in_middle_lines) 
        characters.append(characters_in_end_line) 

    return characters


class AnythingTracker():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_character_range, 
                results_dir, context_line_num, time_file_to_write, turn_off_techniques, expected_character_range=None):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.source_character_range = interest_character_range
        self.interest_character_range  = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
        self.results_dir = results_dir
        self.context_line_num = context_line_num
        self.time_file_to_write = time_file_to_write
        self.turn_off_techniques = turn_off_techniques # SpecifyToTurnOffTechniques object

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
        ''' 
        Step 1: Get all candidate candidates
        * 1.1 git diff changed hunks
        * 1.2 exactly mapped characters
        * 1.3 ...
        '''
        # phrase 1: compute candidate regions starts.
        first_phrase_start_time = time.time()
        # create output folder
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # Read source region characters, and expected regions
        self.base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.file_path)
        self.source_region_characters = get_source_and_expected_region_characters(self.base_file_lines, self.interest_character_range)

        expected_region_characters_str = "<DELETE>"
        self.target_file_lines = checkout_to_read_file(self.repo_dir, self.target_commit, self.file_path)
        if self.expected_character_range != None:
            expected_region_characters: list = get_source_and_expected_region_characters(self.target_file_lines, self.expected_character_range)
            expected_region_characters_str = "".join(expected_region_characters)
        self.write_regions_to_files(expected_region_characters_str, False)
        
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

        # phrase 1: compute candidate regions ends.
        first_phrase_end_time = time.time()
        self.first_phrase_executing_time = "%.3f" % (first_phrase_end_time - first_phrase_start_time)
        print(f"Executing time (1st pharse): {self.first_phrase_executing_time} seconds")

        if candidate_regions == []:
            print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")
            return
        
        self.record_results(candidate_regions)
    
    def record_results(self, candidate_regions):
        # -- write source character to json files
        source_region_characters_str = "".join(self.source_region_characters)
        self.write_regions_to_files(source_region_characters_str)

        output_maps = []

        # -- record candidates
        for candidate in candidate_regions:
            # TODO update to cover rename cases
            target_range = get_candidate_region_range(candidate)
            map = {
                "source_file": self.file_path,
                "target_file": self.file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "target_characters" : candidate.character_sources,
                "kind": candidate.marker
            }
            output_maps.append(map)
        # write candidates to a JSON file.
        candidate_json_file = join(self.results_dir, "candidates.json")
        with open(candidate_json_file, "w") as ds:
            json.dump(output_maps, ds, indent=4, ensure_ascii=False)

        # phrase 2: compute candidate regions starts.
        second_phrase_start_time = time.time()
        # -- Select top-1 candidate from multiple candidates
        # when decided, will focus on only 1 metric
        to_write = []
        results_set_dict = {}
        
        if len(candidate_regions) == 1:
            # phrase 2: compute candidate regions ends.
            self.second_phrase_executing_time = 0
            print(f"Executing time (2nd pharse): 1 candidate, {self.second_phrase_executing_time} seconds")
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
            results_set_dict, average_highest, vote_most = ComputeTargetRegion(source_str, candiate_str_list).run()

            # phrase 2: compute candidate regions ends.
            second_phrase_end_time = time.time()
            self.second_phrase_executing_time = "%.3f" % (second_phrase_end_time - second_phrase_start_time)
            print(f"Executing time (2nd pharse): {self.second_phrase_executing_time} seconds")

            results_set_dict.update(average_highest)
            if vote_most != None:
                results_set_dict.update(vote_most)
        
        for key, target_dict in results_set_dict.items():
            target_candidate = candidate_regions[target_dict["idx"]]
            target_json = {
                "version" : key,
                "source_file": self.file_path,
                "target_file": self.file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_candidate.candidate_region_character_range.four_element_list),
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

        # write target candidate to a single Json file.
        target_json_file = join(self.results_dir, "target.json")
        with open(target_json_file, "w") as ds:
            json.dump(to_write, ds, indent=4, ensure_ascii=False)

        self.record_target_types(results_set_dict, len(candidate_regions))

    def record_target_types(self, results_set_dict, candidate_nums):
        parent_folder, ground_truth_index = self.results_dir.rsplit("/", 1)
        # unique_keys = ["dist_based", "bleu_based", "similarity_based"]
        all_keys = list(results_set_dict.keys())
        dist_based_num = all_keys.count("dist_based")
        bleu_dist_num = all_keys.count("bleu_based")
        dist_based_num = all_keys.count("similarity_based")
        num_str = {
            ground_truth_index : {
                "dist_based": dist_based_num,
                "bleu_based": bleu_dist_num,
                "similarity_based": dist_based_num
            }
        }
        write_mode = "a"
        if ground_truth_index == "0":
            write_mode = "w"

        with open(join(parent_folder, "target_num.json"), write_mode) as f:
            if write_mode == "a":
                f.write(",\n")
            json.dump(num_str, f, indent=4, ensure_ascii=False)

        # write the executing times
        with open(self.time_file_to_write, write_mode) as f:
            csv_writer = csv.writer(f)
            if write_mode == "w":
                csv_writer.writerow(["ground_truth_index", "candidate_numbers", "compute_candidates_executing_time", "select_target_executing_time"])
            csv_writer.writerow([ground_truth_index, candidate_nums, self.first_phrase_executing_time, self.second_phrase_executing_time])
            

if __name__ == "__main__":
    args = parser.parse_args()
    AnythingTracker(args.repo_dir, args.base_commit, args.target_commit, args.file_path, 
            args.source_character_range, args.results_dir, args.context_line_num, args.time_file_to_write, args.turn_off_techniques).run()