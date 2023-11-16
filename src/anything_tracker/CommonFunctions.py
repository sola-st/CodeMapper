from anything_tracker.LineMap import LineMap


def all_elements_to_maps(line_number_list, line_source_list, not_empty_version):
    # not_empty_version: "base" or "target"
    line_level_maps = []
    if not_empty_version == "base":
        for num, source in zip(line_number_list, line_source_list):
            map = LineMap(num, source, "", "")
            line_level_maps.append(map)
    else:
        for num, source in zip(line_number_list, line_source_list):
            map = LineMap("", "", num, source)
            line_level_maps.append(map)
    return line_level_maps

            
def get_hunk_ranges_from_diff_line(tmp_list, tmp_index, line_symbol):
    tmp = tmp_list[tmp_index].lstrip(line_symbol).split(",")
    start = int(tmp[0])
    step = int(tmp[1])
    end = start + step + 1
    hunk_range = range(start, end)
    return hunk_range, start