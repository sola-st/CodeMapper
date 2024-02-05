def get_absolute_char_position(line, char_index, line_lengths):
    return sum(line_lengths[:line - 1]) + char_index


def longest_common_string(expected_chars, candidate_chars):
    table = [[0] * (len(candidate_chars) + 1) for _ in range(len(expected_chars) + 1)]
    max_length = 0
    end_position = 0

    for i in range(1, len(expected_chars) + 1):
        for j in range(1, len(candidate_chars) + 1):
            if expected_chars[i - 1] == candidate_chars[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
                if table[i][j] > max_length:
                    max_length = table[i][j]
                    end_position = i
            else:
                table[i][j] = 0

    lcs = expected_chars[end_position - max_length:end_position]

    return lcs

def calculate_overlap(expected_location, predicted_location, line_lengths, target_lines_str):
    # Get absolute positions for both start and end of each location
    start_line1, start_char1, end_line1, end_char1 = expected_location
    start_line2, start_char2, end_line2, end_char2 = predicted_location

    expected_start_char = get_absolute_char_position(start_line1, start_char1, line_lengths)
    expected_end_char = get_absolute_char_position(end_line1, end_char1, line_lengths)
    predicted_start_char = get_absolute_char_position(start_line2, start_char2, line_lengths)
    predicted_end_char = get_absolute_char_position(end_line2, end_char2, line_lengths)

    expected_chars = target_lines_str[expected_start_char:expected_end_char+1]
    candidate_chars = target_lines_str[predicted_start_char:predicted_end_char+1]

    lcs = longest_common_string(expected_chars, candidate_chars)

    # overlap percentage
    recall = 0 
    precision = 0
    f1_score = 0

    # distance
    pre_distance = 0
    post_distance = 0
    distance = 0

    if lcs == "": # predicted location quality is poor
        return "-1","-1", "-1", "-1", "-1", "-1" # -1: bad quality
        # may from git diff [without options which can detect movement], it mis-identified that the source region is deleted, 
        # but actually it may be moved to another location.
    
    # overlap percentage
    overlap_num = len(lcs)
    expected_len = expected_end_char - expected_start_char + 1
    recall = overlap_num / expected_len
    formatted_recall = round(recall, 4)

    predicted_len = predicted_end_char - predicted_start_char + 1
    assert predicted_len > 0
    precision = overlap_num / predicted_len
    formatted_precision = round(precision, 4)

    # distance
    base_start_extra = expected_chars.index(lcs) - 1
    base_end_extra = len(expected_chars) - base_start_extra - overlap_num

    candidate_start_extra = candidate_chars.index(lcs) - 1
    candidate_end_extra = len(candidate_chars) - candidate_start_extra - overlap_num

    pre_distance = abs(candidate_start_extra - base_start_extra)
    post_distance = abs(candidate_end_extra - base_end_extra)

    distance = pre_distance + post_distance

    if precision + recall != 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
        formatted_f1_score = round(f1_score, 4)

    return pre_distance, post_distance, distance, formatted_recall, formatted_precision, formatted_f1_score