def get_absolute_char_position(line, char_index, line_lengths):
    return sum(line_lengths[:line - 1]) + char_index


def longest_common_string(base_chars, candidate_chars):
    table = [[0] * (len(candidate_chars) + 1) for _ in range(len(base_chars) + 1)]
    max_length = 0
    end_position = 0

    for i in range(1, len(base_chars) + 1):
        for j in range(1, len(candidate_chars) + 1):
            if base_chars[i - 1] == candidate_chars[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
                if table[i][j] > max_length:
                    max_length = table[i][j]
                    end_position = i
            else:
                table[i][j] = 0

    lcs = base_chars[end_position - max_length:end_position]

    return lcs

def calculate_overlap(location1, location2, line_lengths, target_lines_str):
    # Get absolute positions for both start and end of each location
    start_line1, start_char1, end_line1, end_char1 = location1
    start_line2, start_char2, end_line2, end_char2 = location2

    start_position1 = get_absolute_char_position(start_line1, start_char1, line_lengths)
    end_position1 = get_absolute_char_position(end_line1, end_char1, line_lengths)
    start_position2 = get_absolute_char_position(start_line2, start_char2, line_lengths)
    end_position2 = get_absolute_char_position(end_line2, end_char2, line_lengths)

    base_chars = target_lines_str[start_position1:end_position1+1]
    candidate_chars = target_lines_str[start_position2:end_position2+1]

    lcs = longest_common_string(base_chars, candidate_chars)

    rate = "INIT"
    distance = "INIT"
    if lcs:
        # overlap percentage
        overlap_num = len(lcs)
        base = end_position1 - start_position1 + 1
        if base <= 0:
            print(location1, location2)
            rate = "Wrong_line_indices"
        else:
            rate = overlap_num / base
            rate = format(rate, '.4f')

        # distance
        base_start_extra = base_chars.index(lcs) - 1
        base_end_extra = len(base_chars) - base_start_extra - overlap_num

        candidate_start_extra = candidate_chars.index(lcs) - 1
        candidate_end_extra = len(candidate_chars) - candidate_start_extra - overlap_num

        pre_distance = candidate_start_extra - base_start_extra
        post_distance = candidate_end_extra - base_end_extra

        distance = abs(pre_distance) + abs(post_distance)
    else: 
        distance = "Bad_quality_map"
        rate = "Bad_quality_map"

    return distance, rate