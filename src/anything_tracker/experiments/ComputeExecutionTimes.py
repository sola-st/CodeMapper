import csv
from os.path import join


def read_csv_columns(file_path, columns, num_columns):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            if not any(row) or "total" in row:  # Skip empty lines
                continue
            for i in range(num_columns):
                columns[i].append(float(row[i]))
    return columns

def get_columns_for_a_category(file_path_test, file_path_train, num_columns=5):
    columns = [[] for _ in range(num_columns)]  # Create a list of empty lists for each column
    columns = read_csv_columns(file_path_test, columns, num_columns)
    columns = read_csv_columns(file_path_train, columns, num_columns)
    return columns

def get_and_compute(folder, categories):
    # get all data, combine test and training, get only one big list for a category.
    all_data = []
    for category in categories:
        file_path_test = join(folder, f"execution_time_{category}_test.csv")
        file_path_train = join(folder, f"execution_time_{category}_training.csv")
        columns = get_columns_for_a_category(file_path_test, file_path_train)
        all_data.append(columns)
            
    to_write_lists = [["Category", "sum_1st", "avg_1st", "sum_2nd", "avg_2nd", "sum_total", "avg_total"]]

    # go through the dat list for each category
    for i, list in enumerate(all_data):
        ground_truth_indices, candidate_nums, time_1st, time_2nd, time_total = list
        time_1st_sum = sum(time_1st)
        time_1st_avg = round(time_1st_sum / len(time_1st), 3)

        time_2nd_sum = sum(time_2nd)
        time_2nd_avg = round(time_2nd_sum / len(time_2nd), 3)

        time_total_sum = sum(time_total)
        time_total_avg = round(time_total_sum / len(time_total), 3)

        to_write_lists.append([categories[i], time_1st_sum, time_1st_avg, \
                time_2nd_sum, time_2nd_avg, time_total_sum, time_total_avg])

    # write computation results
    with open(join(folder, "statistic_2.csv"), "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(to_write_lists)

if __name__=="__main__":
    folder = join("data", "results", "execution_time")
    categories = ["attribute", "class", "method", "block", "variable"]
    get_and_compute(folder, categories)