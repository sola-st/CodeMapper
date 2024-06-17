import os
from git.repo import Repo


class GetRanges():
    def __init__(self, repo_dir, commit, file, start_line_number_str, suppression_text):
        self.repo_dir = repo_dir
        self.commit = commit
        self.file= file
        self.start_line_number_str = start_line_number_str
        '''
        suppression_text has multiple values:
        * None
        * end line number for blocks (int)
        * element for variables and attributes (str)
        '''
        self.suppression_text = suppression_text

        self.four_element_range = None # to return

    def run(self):
        repo = Repo(self.repo_dir)
        repo.git.checkout(self.commit, force=True)
        self.get_range()
        return self.four_element_range

    def get_range(self):
        if not os.path.exists(self.file):
            # introduce a new file, the file does not exist in parent commit.
            return
        file_lines = None
        # to handle special characters (French?)
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings_to_try:
            try:
                with open(self.file, "r", encoding=encoding) as f:
                    file_lines = f.readlines()
                break
            except UnicodeDecodeError: # try the next encoding
                print(f"Failed to decode using, {encoding}. {self.commit}:{self.file}")

        assert file_lines != None
        start_line_number = int(self.start_line_number_str)
        start_line_number_idx = start_line_number - 1
        try:
            start_line = file_lines[start_line_number_idx]
        except:
            return # newly added
        
        line_len = len(start_line)
        start_character_abs = line_len - len(start_line.lstrip()) + 1 # pre whitespaces
        end_character_abs = line_len -1
        try: # to get a fine-grained start charcter idx
            idx_hint = start_line.index("pylint")
            before_pylint = start_line[:idx_hint]
            reversed(before_pylint)
            start_character_abs = before_pylint.index("#") + 1
        except:
            # print(f"Line: {self.suppression_text}")
            pass

        end_idx_hint = None
        try: # to get a fine-grained end charcter idx
            end_idx_hint = start_line.index(self.suppression_text)
            # print("fine-grained")
        except:
            pass
        if end_idx_hint != None:
            end_character_abs = end_idx_hint + len(self.suppression_text)

        self.four_element_range = [start_line_number, start_character_abs, start_line_number, end_character_abs]