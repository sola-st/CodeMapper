import csv
import json
import matplotlib.pyplot as plt
from os.path import join

import numpy as np
from anything_tracker.visualization.PlotExexutionTimeComparison import get_execution_time


def get_size_list(size_file):
    size_list = []
    with open(size_file) as f:
        maps = json.load(f)
    for m in maps:
        size_list.append(m["region_size"])
    return size_list

def get_execution_time(time_file):
    with open(time_file, "r") as f:
        csv_reader = csv.reader(f)
        line_list = list(csv_reader)[1:]

    times_1 = [float(line[2]) for line in line_list]
    times_2 = [float(line[3]) for line in line_list]
    return times_1, times_2

def plot_source_region_size_and_time_3d(size_list, times_1, times_2, result_pdf):
    # Three axes scatter plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(size_list, times_1, times_2)
    ax.set_xlabel('Source region size')
    ax.set_ylabel('Phase 1')
    ax.set_zlabel('Phase 2')
    # plt.title('Relationship between Source region Size and Execution Time')
    plt.tight_layout()
    plt.savefig(result_pdf)

def plot_source_region_size_and_time_2d(size_list, times_1, times_2, result_pdf):
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.scatter(size_list, times_1)
    plt.xlabel('Source region size')
    plt.ylabel('Phase 1 execution time (seconds)')
    num = int(max(times_1)) + 1
    y_ticks_sub_time1 = np.linspace(0, num, 10)
    plt.yticks(y_ticks_sub_time1)

    plt.subplot(1, 2, 2)
    plt.scatter(size_list, times_2)
    plt.xlabel('Source region size')
    plt.ylabel('Phase 2 execution time (seconds)')

    plt.tight_layout()
    plt.savefig(result_pdf)


if __name__=="__main__":
    result_pdf = join("data", "results", "table_plots", "execution_time_size_corelationship.pdf")
    execution_time_folder = join("data", "results", "execution_time")
    region_size_folder = join("data", "results", "table_plots")
    data_type = ["annodata", "suppression"]

    times_1 = [] 
    times_2 = []
    region_sizes = []

    for t in data_type:
        # execution time
        execution_time_file_anno = join(execution_time_folder, t, f"execution_time_{t}.csv")
        sub_times_1, sub_times_2 = get_execution_time(execution_time_file_anno)
        times_1.extend(sub_times_1)
        times_2.extend(sub_times_2)

        # source region size
        source_region_size_file = join(region_size_folder, f"region_size_meta_{t}.json")
        sub_sizes = get_size_list(source_region_size_file)
        region_sizes.extend(sub_sizes)

    plot_source_region_size_and_time_3d(region_sizes, times_1, times_2, result_pdf)