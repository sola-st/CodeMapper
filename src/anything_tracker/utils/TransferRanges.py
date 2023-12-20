def transfer_2_indices_to_4(given_start_character_idx, given_end_character_idx, source_lines_len_list):
    '''
    Web UI connection specific.
    Transfer the location range for picked up source regions.
    # 2: absolute character indices | [start, end]
    # 4: line and character indices | [start_line, start_char., end_line, end_char]
    '''

    # To return
    start_line_idx = None
    end_line_idx= None
    start_character_idx = None
    end_character_idx = None

    pre_location = 0
    current_location = 0

    for line_idx, length in enumerate(source_lines_len_list):
        current_location +=length
        current_location_border = current_location + 1
        if given_start_character_idx in range(pre_location, current_location_border) and start_line_idx == None:
            start_line_idx = line_idx + 1
            start_character_idx = given_start_character_idx - pre_location
        if given_end_character_idx in range(pre_location, current_location_border) and end_line_idx == None:
            end_line_idx = line_idx + 1
            end_character_idx = given_end_character_idx - pre_location

        if start_line_idx and end_line_idx:
            region_range = [start_line_idx, start_character_idx, end_line_idx, end_character_idx]
            return region_range
        
        pre_location = current_location