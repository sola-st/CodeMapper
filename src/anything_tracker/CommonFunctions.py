from anything_tracker.HunkMap import HunkMap
from anything_tracker.LineMap import LineMap


def all_elements_to_line_maps(bases, targets, not_empty_version):
    # not_empty_version: "base" or "target"
    maps = []
    if not_empty_version == "base":
        for base in bases:
            map = LineMap(base, None)
            maps.append(map)
    else:
        for target in targets:
            map = LineMap(None, target)
            maps.append(map)
    return maps

def all_elements_to_hunk_maps(bases, targets, not_empty_version):
    # not_empty_version: "base" or "target"
    maps = []
    if not_empty_version == "base":
        for base in bases:
            map = HunkMap(base, None)
            maps.append(map)
    else:
        for target in targets:
            map = HunkMap(None, target)
            maps.append(map)
    return maps

def get_hunk_ranges_from_diff_line(tmp_list, tmp_index, line_symbol):
    tmp = tmp_list[tmp_index].lstrip(line_symbol).split(",")
    start = int(tmp[0])
    step = int(tmp[1])
    end = start + step + 1
    hunk_range = range(start, end)
    return hunk_range, start