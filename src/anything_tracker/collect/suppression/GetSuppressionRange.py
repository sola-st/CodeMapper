import re
from git.repo import Repo
from anything_tracker.collect.suppression.SuppressionTypeNumericMaps import get_mapping_numeric_code


class GetSuppressionRange():
    "Return the found range, and the region characters."
    def __init__(self, maps, repo_dir, commit, file, line_number, suppression_text,
                add_event_only_suppression_type, suppression_type=None):
        self.maps = maps
        self.repo_dir = repo_dir
        self.commit = commit
        self.file= file
        self.line_number = line_number
        self.add_event_only_suppression_type = add_event_only_suppression_type
        self.suppression_text = suppression_text # e.g., # pylint: disable=invalid-name
        self.suppression_type = suppression_type #e.g., invalid-name

    def run(self):   
        repo = Repo(self.repo_dir)
        repo.git.checkout(self.commit, force=True)

        file_lines = None
        # Read files. To handle special characters (French?)
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings_to_try:
            try:
                with open(self.file, "r", encoding=encoding) as f:
                    file_lines = f.readlines()
                break
            except UnicodeDecodeError: # try the next encoding
                print(f"Failed to decode using, {encoding}. {self.commit}:{self.file}")

        assert file_lines != None
        line_number_idx = self.line_number - 1
        suppression_line = file_lines[line_number_idx]

        '''
        check how the suppression stays in the line, 4 senarios:
        1) the entire suppression_text is in the line (may some differs on whitespaces).
        2) the suppression type is numeric code.
        3) the suppression is in suppression type set (type).
        4) the suppression is in suppression type set (numeric).
        '''
        
        start_character_abs = 0
        end_character_abs = 0
        suppression_line_splits = suppression_line.split(" ")
        # handle the mismatches caused by whitespaces
        clean = [re.sub(r"[^\w\s]", "", s).strip() for s in suppression_line_splits]

        # get the start character location
        start_split_idx_tmp = None
        start_split_idx = None
        for idx, split in enumerate(clean):
            if "pylint" in split: # the split can be "#pylint..." or "pylint..."
                start_split_idx_tmp = idx
                pylint_idx = split.index("pylint")
                if pylint_idx != 0: # the "#" may in the same split
                    if split[pylint_idx-1] == "#":
                        start_split_idx = idx
                break
        
        if start_split_idx_tmp == None: # inaccurate history
            return None, None, None
        
        if not start_split_idx:
            start_split_idx = start_split_idx_tmp -1 # the "#" in the previous split
            while start_split_idx > -1:
                if suppression_line_splits[start_split_idx][-1] != "#":
                    start_split_idx-=1 # go to the previous until it finds a #.
                else:
                    break
        
        start_character_abs = len(" ".join(suppression_line_splits[:start_split_idx])) + 1
        start_split = suppression_line_splits[start_split_idx]
        reversed(start_split)
        end_delta = start_split.index("#")
        start_character_abs += (len(start_split) - end_delta) - 1
        while suppression_line[start_character_abs-1] != "#":
            start_character_abs += 1

        # get the end character location
        current_only_suppression_type = False
        truncated_line = suppression_line[(start_character_abs-1):].rstrip()
        if self.suppression_type not in truncated_line: 
            numeric_code = get_mapping_numeric_code(self.maps, self.suppression_type)
            self.suppression_type = numeric_code

        if truncated_line.endswith(self.suppression_type) and not "," in truncated_line and \
                self.add_event_only_suppression_type == False: # scenario 1 or 2
            end_character_abs = start_character_abs + len(truncated_line) - 1
        else: # scenario 3 or 4
            # move to foucs on only the suppression type
            start_character_abs += truncated_line.index(self.suppression_type)
            if suppression_line[start_character_abs-1].isalnum() == False:
                start_character_abs += 1
            end_character_abs = start_character_abs + len(self.suppression_type) -1
            current_only_suppression_type = True

        four_element_range = [self.line_number, start_character_abs, self.line_number, end_character_abs]
        suppression_characters = suppression_line[start_character_abs-1: end_character_abs]
        return four_element_range, suppression_characters, current_only_suppression_type