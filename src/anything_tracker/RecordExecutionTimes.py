import csv
from anything_tracker.OneRoundTimeInfo import get_time_relevant_names


class RecordExecutionTimes():
    # For AnythingTrackerOnHistoryPairs
    def __init__(self, write_mode, time_file_to_write, ground_truth_index, \
                one_round_time_info, current_history_pair_idx=None):
        self.write_mode = write_mode
        self.time_file_to_write = time_file_to_write
        self.one_round_time_info = one_round_time_info
        self.current_history_pair_idx = current_history_pair_idx
        self.times_to_write = [ground_truth_index]

    def write_execution_time(self):
        # prepare the time data for writing
        overall_time = float(self.one_round_time_info.compute_candidates_time) + float(self.one_round_time_info.select_target_time)
        self.one_round_time_info.overall_time = overall_time

        # ge t all time relevant numbers as a list
        time_list = [getattr(self.one_round_time_info, attr) for attr in self.one_round_time_info.__annotations__]
        self.times_to_write.extend(time_list)

        with open(self.time_file_to_write, self.write_mode) as f:
            csv_writer = csv.writer(f)
            if self.write_mode == "w":
                header = ["ground_truth_idx"]
                time_names = get_time_relevant_names()
                header.extend(time_names)
                csv_writer.writerow(header)
            elif self.current_history_pair_idx == "0":
                f.write("\n")
            csv_writer.writerow(self.times_to_write)
            
    def run(self):
        self.write_execution_time()
