class DiffHunk():
    def __init__(self, base_start_line_number, base_end_line_number, 
                 target_start_line_number, target_end_line_number):
        self.base_start_line_number = base_start_line_number
        self.base_end_line_number = base_end_line_number
        self.target_start_line_number = target_start_line_number
        self.target_end_line_number = target_end_line_number