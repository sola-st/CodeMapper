class LineMap():
    def __init__(self, base_line_number, base_line_source, target_line_number, target_line_source):
        self.base_line_number = base_line_number
        self.base_line_source = base_line_source
        self.target_line_number = target_line_number
        self.target_line_source = target_line_source

def show_maps(__value: object):
    print(f"[{__value.base_line_number}, {__value.base_line_source}]")
    print("maps to")
    print(f"[{__value.target_line_number}, {__value.target_line_source}]")