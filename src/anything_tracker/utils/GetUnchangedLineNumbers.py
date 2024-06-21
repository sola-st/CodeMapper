from anything_tracker.utils.TransferRanges import get_diff_reported_range


def get_first_and_last_unchanged_line_numbers(interest_line_numbers, specified_diff_hunks, first=True, last=True):
        # get all the no changed line numbers
        changed_line_numbers = []
        for hunk in specified_diff_hunks:
            hunk_range = range(hunk.base_start_line_number, hunk.base_end_line_number)
            changed_line_numbers.extend(list(hunk_range))
        unchanged_line_numbers = list(set(interest_line_numbers) - set(changed_line_numbers))
        unchanged_line_numbers.sort()
        for hunk in specified_diff_hunks:
            if hunk.base_start_line_number == hunk.base_end_line_number:
                break_point = unchanged_line_numbers.index(hunk.base_start_line_number) + 1
                unchanged_line_numbers.insert(break_point, -2)
        unchanged_num = len(unchanged_line_numbers)

        # Forward iteration, get first_unchanged_line_numbers
        if first == True:
            first_unchanged_line_numbers = [] 
            for i in range(unchanged_num):
                if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] + 1:
                    if first_unchanged_line_numbers:
                        break
                    else:
                        first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 
                else:
                    first_unchanged_line_numbers.append(unchanged_line_numbers[i]) 
            assert first_unchanged_line_numbers != []

        # Backward iteration, get last_unchanged_line_numbers
        if last == True:
            last_unchanged_line_numbers = []
            unchanged_line_numbers.reverse()
            for i in range(unchanged_num):
                if unchanged_line_numbers[i] != unchanged_line_numbers[i-1] - 1:
                    if last_unchanged_line_numbers:
                        break
                    else:
                        last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i]) 
                else:
                    last_unchanged_line_numbers.insert(0, unchanged_line_numbers[i])
            assert last_unchanged_line_numbers != []
        
        if first == True and last == True:
            return first_unchanged_line_numbers, last_unchanged_line_numbers
        elif first == True and last == False:
            return first_unchanged_line_numbers
        elif first == False and last == True:
            return last_unchanged_line_numbers
        

def get_changed_line_numbers_file_level(diff_result):
    '''
    Iterate through the diff reports, and get all the changed line numbers.
    '''
    changed_line_numbers_source = []
    changed_line_numbers_target = []

    if not diff_result:
        # the source range is not changed
        return changed_line_numbers_source, changed_line_numbers_target
        
    diffs = diff_result.split("\n")
    for diff_line in diffs:
        diff_line = diff_line.strip()
        if "\033[36m" in diff_line:
            tmp = diff_line.split(" ")
            base_meta_range = tmp[1]
            base_hunk_range, step, abd_end = get_diff_reported_range(base_meta_range)
            changed_line_numbers_source.extend(list(base_hunk_range))
            target_meta_range = tmp[2]
            target_hunk_range, step = get_diff_reported_range(target_meta_range, False)
            changed_line_numbers_target.extend(list(target_hunk_range))
    
    return changed_line_numbers_source, changed_line_numbers_target