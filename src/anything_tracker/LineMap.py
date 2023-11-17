from anything_tracker.Line import show_line


class LineMap():
    def __init__(self, base_line, target_line):
        self.base_line = base_line
        self.target_line = target_line

def show_line_map(__value: object):
    print("--------------------------------------------")
    show_line(__value.base_line)
    print("maps to")
    show_line(__value.target_line)
    print("--------------------------------------------")
    print()