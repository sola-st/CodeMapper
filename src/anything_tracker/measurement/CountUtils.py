import json


def count_algorithms(change):
    algorithms = ["default", "minimal", "patience", "histogram"]
    algorithm_count = {}
    for a in algorithms:
        num = len([c for c in change if a in c])
        algorithm_count.update({a: num})

    algorithm_count_str = json.dumps(algorithm_count)
    change.append(algorithm_count_str)
    return change

def count_exact_matches(is_matched_set):
    y_num = is_matched_set.count("Y")
    m_num = is_matched_set.count("M")
    w_num = is_matched_set.count("W")
    match_dict = {
        "Y": y_num, 
        "M": m_num, 
        "W": w_num
    }
    
    match_str = json.dumps(match_dict)
    is_matched_set.append(match_str)
    return is_matched_set


def clear_none_values(list):
    cleared_list = [val for val in list if val]
    return cleared_list