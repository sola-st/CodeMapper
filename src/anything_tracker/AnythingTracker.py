import argparse
import json
import os
from os.path import join
from anything_tracker.CandidateRegion import get_candidate_region_range
from anything_tracker.CharacterRange import CharacterRange
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


class AnythingTracker():
    def __init__(self, repo_dir, base_commit, target_commit, file_path, interest_character_range, results_dir):
        self.repo_dir = repo_dir
        self.base_commit = base_commit
        self.target_commit = target_commit
        self.file_path = file_path
        self.source_character_range = interest_character_range
        self.interest_character_range = character_range_init = CharacterRange(interest_character_range)
        interest_line_range = character_range_init.character_range_to_line_range() # all numbers starts at 1.
        self.interest_line_numbers = list(interest_line_range)
        self.results_dir = results_dir

        self.source_region_characters = []

    def get_source_region_characters(self):
        '''
        Initially get self.source_region_characters.
        '''

        base_file_lines = checkout_to_read_file(self.repo_dir, self.base_commit, self.file_path)

        # interest_character_range: start_line, start_character, end_line, end_character
        start_line_idx = self.interest_character_range.start_line_idx
        characters_start_idx = self.interest_character_range.characters_start_idx
        end_line_idx = self.interest_character_range.end_line_idx
        characters_end_idx = self.interest_character_range.characters_end_idx

        start_line = str(base_file_lines[start_line_idx-1])

        if start_line_idx == end_line_idx: 
            # source region inside one line.
            # source region only records one line number, that is, the start and end are on the same line.
            self.source_region_characters = start_line[characters_start_idx-1 : characters_end_idx]
        else:
            # source region covers multi-line
            # separate to 3 sections: start line, middle lines, and end line.
            # section 1: start line : the entire line is covered
            characters_in_start_line = start_line[characters_start_idx-1:] 
        
            # section 2: middle lines : all covered
            characters_in_middle_lines= []
            if start_line_idx + 1 != end_line_idx:
                characters_in_middle_lines = base_file_lines[start_line_idx : end_line_idx - 1]

            # section 3: end line : [character index [0: specified_index]]
            end_line = str(base_file_lines[end_line_idx-1]) 
            characters_in_end_line = end_line[:characters_end_idx]

            self.source_region_characters.append(characters_in_start_line) 
            self.source_region_characters.extend(characters_in_middle_lines) 
            self.source_region_characters.append(characters_in_end_line) 
        
        # write source characters to a JSON file.
        source_region_characters_str = "".join(self.source_region_characters)
        source = {
            "source_file": self.file_path,
            "source_range": str(self.source_character_range),
            "source_characters": source_region_characters_str
        }
        source_json_file = join(self.results_dir, "source.json")
        with open(source_json_file, "w") as ds:
            json.dump(source, ds, indent=4, ensure_ascii=False)

    def run(self):
        ''' 
        Step 1: Get all candidate candidates
        * 1.1 git diff changed hunks
        * 1.2 exactly mapped characters
        * 1.3 ...
        '''
        # create output folder
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        output_maps = []
        candidate_regions = []

        # Read source region characters, write source character to json files.
        self.get_source_region_characters()
        # get candidates from git diff
        diff_candidates, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks = GitDiffToCandidateRegion(self).run_git_diff()
        # search to map characters
        search_candidates = SearchLinesToCandidateRegion(self, top_diff_hunks, middle_diff_hunks, bottom_diff_hunks).search_maps()
        candidate_regions.extend(diff_candidates)
        candidate_regions.extend(search_candidates)
        if candidate_regions == []:
            print(f"--No candidate regions.\n  {self.repo_dir}\n  {self.file_path}\n  {self.interest_character_range.four_element_list}\n")
            return
        
        for candidate in candidate_regions:
            # TODO update to cover rename cases
            target_range= get_candidate_region_range(candidate)
            map = {
                "source_file": self.file_path,
                "target_file": self.file_path,
                "source_range": str(self.source_character_range),
                "target_range": str(target_range),
                "target_characters" : candidate.character_sources,
                "kind": candidate.marker
            }
            output_maps.append(map)

        # TODO Other steps

        # write candidates to a JSON file.
        candidate_json_file = join(self.results_dir, "candidates.json")
        with open(candidate_json_file, "w") as ds:
            json.dump(output_maps, ds, indent=4, ensure_ascii=False)
 

if __name__ == "__main__":
    args = parser.parse_args()
    AnythingTracker(args.repo_dir, args.base_commit, args.target_commit, args.file_path, args.source_character_range, args.results_dir).run()