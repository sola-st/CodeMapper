import csv
import matplotlib.pyplot as plt
from os.path import join
from scipy import stats
import numpy as np


def read_time_file(time_csv_file):
    with open(time_csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row if exists
        execution_times_1st_phrase = []
        execution_times_2nd_phrase = []
        candidate_nums = []
        # Read each row and extract the second column
        for row in reader:
            candidate_nums.append(int(row[1]))
            execution_times_1st_phrase.append(float(row[2]))
            execution_times_2nd_phrase.append(float(row[3]))
    
    return candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase

def calculation(data):
    median = np.median(data)
    avg = np.average(data)
    max = np.max(data)
    min = np.min(data)
    return median, avg, max, min

def get_candidates_numbers(executuion_times, max_time, min_time, candi_nums):
    candi_num_max = candi_nums[executuion_times.index(max_time)]
    candi_num_min = candi_nums[executuion_times.index(min_time)]
    return candi_num_max, candi_num_min


class PlotExecutionTimes():
    def __init__(self, font_size, time_csv_file, plot_output):
        plt.rcParams.update({'font.size': font_size})
        self.time_csv_file = time_csv_file
        self.plot_output = plot_output

    def plot_times(self, candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase):
        # Calculate for each set of execution times
        # candi_num_avg = np.average(candidate_nums)
        median_time_1, avg_time_1, max_time_1, min_time_1 = calculation(execution_times_1st_phrase)
        median_time_2, avg_time_2, max_time_2, min_time_2 = calculation(execution_times_2nd_phrase)
        # candi_num_max_1, candi_num_min_1 = get_candidates_numbers(\
        #         execution_times_1st_phrase, max_time_1, min_time_1, candidate_nums)
        # candi_num_max_2, candi_num_min_2 = get_candidates_numbers(\
        #         execution_times_2nd_phrase, max_time_2, min_time_2, candidate_nums)

        # Create subplots with 1 row and 2 columns
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Box plot for execution_times_1st_phrase 1
        axes[0].boxplot(execution_times_1st_phrase)
        # axes[0].set_title('Execution Times for Runnuing Phrase 1')
        axes[0].set_ylabel('Execution Time (seconds)')
        axes[0].set_xticklabels([''])  # Set empty x-label
        # Add annotations
        axes[0].text(0.95, median_time_1, f'Median: {median_time_1:.3f}', horizontalalignment='right', verticalalignment='center')
        axes[0].text(1.1, avg_time_1, f'Avg: {avg_time_1:.3f}', horizontalalignment='left', verticalalignment='center')
        axes[0].text(1.1, max_time_1, f'Max: {max_time_1:.3f}', horizontalalignment='left', verticalalignment='center') #  | {candi_num_max_1}
        axes[0].text(1.1, min_time_1, f'Min: {min_time_1:.3f}', horizontalalignment='left', verticalalignment='center') #  | {candi_num_min_1}

        # Box plot for execution_times_2nd_phrase
        axes[1].boxplot(execution_times_2nd_phrase)
        # axes[1].set_title('Execution Times for Runnuing Phrase 2')
        # axes[1].set_ylabel('Execution Time (seconds)')
        axes[1].set_xticklabels([''])
        axes[1].text(0.95, median_time_2, f'Median: {median_time_2:.3f}', horizontalalignment='right', verticalalignment='center')
        axes[1].text(1.1, avg_time_2, f'Avg: {avg_time_2:.3f}', horizontalalignment='left', verticalalignment='bottom')
        axes[1].text(1.1, max_time_2, f'Max: {max_time_2:.3f}', horizontalalignment='left', verticalalignment='center') #  | {candi_num_max_2}
        axes[1].text(1.1, min_time_2, f'Min: {min_time_2:.3f}', horizontalalignment='left', verticalalignment='center')  # | {candi_num_min_2}
        plt.tight_layout()
        plt.savefig(self.plot_output)

    def plot_correlationship(self, candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase):
        # Create subplots with 1 row and 2 columns
        fig, axes = plt.subplots(2, 1, figsize=(12, 12))

        # Plot 1: Execution Times 1 vs Candidate Numbers
        slope_1, intercept_1, _, _, _ = stats.linregress(candidate_nums, execution_times_1st_phrase)
        axes[0].scatter(candidate_nums, execution_times_1st_phrase)
        axes[0].plot(candidate_nums, slope_1 * np.array(candidate_nums) + intercept_1, color='blue', linewidth=2, label='Trendline')
        # axes[0].set_title('Execution Times 1st Phrase vs Candidate Numbers')
        # axes[0].set_xlabel('Candidate Numbers')
        axes[0].set_ylabel('Execution Time')
        axes[0].legend()

        # Plot 2: Execution Times 2 vs Candidate Numbers
        slope_2, intercept_2, _, _, _ = stats.linregress(candidate_nums, execution_times_2nd_phrase)
        axes[1].scatter(candidate_nums, execution_times_2nd_phrase)
        axes[1].plot(candidate_nums, slope_2 * np.array(candidate_nums) + intercept_2, color='blue', linewidth=2, label='Trendline')
        # axes[1].set_title('Execution Times 2nd Phrase vs Candidate Numbers')
        axes[1].set_xlabel('Candidate Numbers')
        axes[1].set_ylabel('Execution Time')
        # axes[1].legend()

        plt.tight_layout()
        plt.savefig(self.plot_output.replace(".pdf", "_correlationship.pdf"))

    def run(self):
        candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase = read_time_file(self.time_csv_file)
        self.plot_times(candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase)
        self.plot_correlationship(candidate_nums, execution_times_1st_phrase, execution_times_2nd_phrase)


if __name__=="__main__":
    font_size = 22
    time_csv_file = join("data", "results", "executing_time_4_metrics.csv")
    plot_output = join("data", "results", "table_plots", "executing_time.pdf")
    PlotExecutionTimes(font_size, time_csv_file, plot_output).run()
