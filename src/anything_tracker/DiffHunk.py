class DiffHunk():
    def __init__(self, base_start_line_number, base_end_line_number, 
                 target_start_line_number, target_end_line_number,
                 target_start_character, target_end_character):
        # all numbers are start at 1
        # end_line_numbers is right open range number, all the others are exactly the location numbers
        self.base_start_line_number = base_start_line_number 
        self.base_end_line_number = base_end_line_number 
        self.target_start_line_number = target_start_line_number
        self.target_end_line_number = target_end_line_number
        self.target_start_character = target_start_character
        self.target_end_character = target_end_character