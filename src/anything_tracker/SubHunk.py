class SubHunk():
    def __init__(self, line_numbers:list, line_sources:list):
        self.line_numbers = line_numbers
        self.line_sources = line_sources

def show_hunk(__value: object):
    print(f"{__value.line_numbers}, {__value.line_sources}")