from anything_tracker.Line import Line


class Hunk():
    def __init__(self, line_numbers:list, line_sources:list):
        self.line_numbers = line_numbers
        self.line_sources = line_sources

        lines = []
        for num, source in zip(line_numbers, line_sources):
            line = Line(num, source)
            lines.append(line)

        self.lines = lines
    

def show_hunk(__value: object):
    for line in __value.lines:
        print(f"{line.number}, {line.source}")