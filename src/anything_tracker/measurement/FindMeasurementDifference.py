import csv
from os.path import join


def get_target_range_and_match_results(files):
    common_meta_lines = []
    ranges_and_matches = []
    for file in files:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            all_lines = [line for line in line_list if line][1:-1] # 1 head, 1 summary
            ranges = [line[6] for line in all_lines]
            matches = [line[7] for line in all_lines]
            ranges_and_matches.append(ranges)
            ranges_and_matches.append(matches)

    common_meta_lines = [line[:6] for line in all_lines]
    return common_meta_lines, ranges_and_matches

def tell_the_differences(common_meta_lines, ranges_and_matches, results_csv_file):
    range_line, matches_line, range_word, matches_word, range_at, matches_at = ranges_and_matches

    different_cases = []
    header_line = ["Ground idx", "Candi_num", "idx", "commit", \
            "Change_marker", "Expected", "Line", "", "Word", "", "AnythingTracker", ""]
    different_cases.append(header_line)

    i = 0
    for match_line, match_word, match_at in zip(matches_line, matches_word, matches_at):
        match_set = set([match_line, match_word, match_at])
        # if not "Y" in match_set:  # closer matching
        if len(match_set) > 1: # the results differ
        # if len(match_set) > 1 and match_at == "Y": # only anythingtracker
        # if match_line == match_word == "Y":
            # different_cases.append
            case_data = common_meta_lines[i]
            case_data.append(range_line[i])
            case_data.append(matches_line[i])
            case_data.append(range_word[i])
            case_data.append(matches_word[i])
            case_data.append(range_at[i])
            case_data.append(matches_at[i])
            different_cases.append(case_data)
        i+=1
    
    with open(results_csv_file, "w") as f:
        csv_writer = csv.writer(f)
        for row in different_cases:
            csv_writer.writerow(row)


def annotated_data_main(common_folder):
    # annotated data
    common = join(common_folder, "annodata")
    results_csv_file = join(common, "different_cases.csv")
    file_name_base = "measurement_results_metrics_annodata"
    file_list = [
            join(common, f"{file_name_base}_line.csv"),
            join(common, f"{file_name_base}_word.csv"),
            join(common, f"{file_name_base}.csv")]
    common_meta_lines, ranges_and_matches = get_target_range_and_match_results(file_list)
    tell_the_differences(common_meta_lines, ranges_and_matches, results_csv_file)

def suppression_main(common_folder):
    # suppression data
    common = join(common_folder, "suppression")
    results_csv_file = join(common, "different_cases.csv")
    file_name_base = "measurement_results_metrics_suppression"
    file_list = [
            join(common, f"{file_name_base}_line.csv"),
            join(common, f"{file_name_base}_word.csv"),
            join(common, f"{file_name_base}.csv")]
    common_meta_lines, ranges_and_matches = get_target_range_and_match_results(file_list)
    tell_the_differences(common_meta_lines, ranges_and_matches, results_csv_file)


if __name__=="__main__":
    common_folder = join("data", "results", "measurement_results")
    annotated_data_main(common_folder)
    suppression_main(common_folder)