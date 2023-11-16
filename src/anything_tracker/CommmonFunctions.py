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