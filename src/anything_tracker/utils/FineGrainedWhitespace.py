def count_leading_whitespace(string:str, target_char:str):
    count = 0
    for char in string:
        if char == target_char:
            count += 1
        else:
            break  # Stop counting when a non-whitespace character is encountered
    return count


def fine_grained_changes(source_1st_line_str, candidate_1st_line_str, check_char):
    whitespace_num_in_source = 0
    whitespace_num_in_candidate = 0

    # get the number of whitespace in source
    if source_1st_line_str.startswith(check_char):
        whitespace_num_in_source = count_leading_whitespace(source_1st_line_str, check_char)

    # get the number of whitespace in changed hunk target side
    if candidate_1st_line_str.startswith(check_char):
        whitespace_num_in_candidate = count_leading_whitespace(candidate_1st_line_str, check_char)

    lstrip_num = None
    if whitespace_num_in_source != whitespace_num_in_candidate:
        lstrip_num = whitespace_num_in_candidate - whitespace_num_in_source
        if lstrip_num < 0:
            lstrip_num = None # Always return None or a number which is > 0
    return lstrip_num