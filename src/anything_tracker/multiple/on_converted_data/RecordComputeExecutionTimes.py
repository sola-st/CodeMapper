import csv


class RecordComputeExecutionTimes():
    '''
    Expected recorded execution time format:
        For the 1st round/iteration: "ground_truth_index", "candidate_numbers", "time_1st", "time_2nd", "overall"
        For the 2nd round/iteration: "ground_truth_index", "candidate_numbers", "time_1st", "time_2nd", "overall"
        For the 3rd round/iteration: "ground_truth_index", "candidate_numbers", "time_1st", "time_2nd", "overall"
        ... (all the remaining rounds)

        Overall for this peice of date: 
            "", "", "time_1st_sum", "time_2nd_sum", "overall_sum(the total exution time for current peice of data)"

    Note: all the overall are calulated without "Round", the results are rounded later.
    eg,. "time_1st" = 0.1296542, "time_2nd" = 1.0245334, the overall = round(0.1296542 + 1.0245334)
    And the final result csv will show:
    time_1st" = 0.130, "time_2nd" = 1.025, the overall all with 3 digits.
    '''

    def __init__(self, write_mode, time_file_to_write, indices, candi_nums, times_1st, times_2nd):
        self.write_mode = write_mode
        self.time_file_to_write = time_file_to_write
        self.indices = indices
        self.candi_nums = candi_nums
        self.times_1st = times_1st
        self.times_2nd = times_2nd

        self.digits = 3 # to format the numbers, keep 3 digits.
        self.times_to_write = [] # to write

    def get_computation_results(self, time_list):
        time_sum = round(sum(time_list), self.digits)
        time_max = round(max(time_list), self.digits)
        time_min = round(min(time_list), self.digits)
        time_avg = round((time_sum / len(time_list)), self.digits)
        return f"Sum: {time_sum}\nMax: {time_max}\nMin: {time_min}\nAvg: {time_avg}"

    def compute_one_round_overall_time(self):
        times_round_level_overall = []
        for idx, num, t1, t2 in zip(self.indices, self.candi_nums, self.times_1st, self.times_2nd):
            overall = round((t1 + t2), self.digits)
            times_round_level_overall.append(overall)
            self.times_to_write.append([idx, num, t1, t2, overall])

        overall_for_current_data = [
            None, 
            None, 
            self.get_computation_results(self.times_1st), 
            self.get_computation_results(self.times_2nd), 
            self.get_computation_results(times_round_level_overall)
        ]
        self.times_to_write.append(overall_for_current_data)

    def write_execution_time(self):
        with open(self.time_file_to_write, self.write_mode) as f:
            csv_writer = csv.writer(f)
            if self.write_mode == "w":
                csv_writer.writerow(["ground_truth_index", "candidate_numbers", \
                        "compute_candidates_executing_time", "select_target_executing_time", "total"])
            for row in self.times_to_write:
                csv_writer.writerow(row)
            f.write("\n")

    def run(self):
        self.compute_one_round_overall_time()
        self.write_execution_time()
