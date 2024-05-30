import csv


class RecordExecutionTimes():
    # For AnythingTrackerOnHistoryPairs
    def __init__(self, write_mode, time_file_to_write, ground_truth_index, \
                candi_num, times_1st, times_2nd, current_history_pair_idx=None):
        self.write_mode = write_mode
        self.time_file_to_write = time_file_to_write
        self.current_history_pair_idx = current_history_pair_idx

        digits = 3 # to format the numbers, keep 3 digits.
        overall_time = round((times_1st + times_2nd), digits)
        self.times_to_write = [ground_truth_index, candi_num, times_1st, times_2nd, overall_time]

    def write_execution_time(self):
        with open(self.time_file_to_write, self.write_mode) as f:
            csv_writer = csv.writer(f)
            if self.write_mode == "w":
                csv_writer.writerow(["ground_truth_index", "candidate_numbers", \
                        "compute_candidates_executing_time", "select_target_executing_time", "total"])
            elif self.current_history_pair_idx == "0":
                f.write("\n")
            csv_writer.writerow(self.times_to_write)
            
    def run(self):
        self.write_execution_time()
