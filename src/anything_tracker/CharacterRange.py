class CharacterRange():
    def __init__(self, four_element_list):
        '''
        Represent any character ranges. 
        It can be source region's or candidate region's, or a character range in a single line.
        Original given number in four_element_list starts at 0.
        '''

        self.four_element_list = four_element_list
        self.start_line_idx : int = four_element_list[0]
        self.characters_start_idx : int = four_element_list[1]
        self.end_line_idx : int = four_element_list[2]
        self.characters_end_idx : int = four_element_list[3]

    def character_range_to_line_range(self):
        interest_line_range = range(self.start_line_idx, self.end_line_idx + 1)
        return interest_line_range

def show_character_range(__value: object):
    print(f"region character range: {__value.four_element_list}")
    

class CandidateCharacterRangeCombinationReminder():
    def __init__(self, character_range:list, is_line_end_covered=False):
        '''
        * character_range: for candidate regions and for a single line. eg,. [2, 6, 2, 30]
        * is_line_end_covered: used to show if the current line can be combined to other candidate lines.
        '''
        self.character_range = CharacterRange(character_range)
        self.is_line_end_covered = is_line_end_covered 