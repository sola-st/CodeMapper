import csv
import json
from os.path import join
from os import makedirs
from anything_tracker.measurement.MeasureAnnotatedData import calculation_helper

# def category_languages():
#     default = ["Python", "Java", "JavaScript", "C#", "C++", "Go", "Ruby", "TypeScript", "PHP", "HTML"]

def process(file_type, cols):
    is_matched_list = cols[7]
    y_num = is_matched_list.count("Y")
    m_num = is_matched_list.count("M")
    w_num = is_matched_list.count("W")
    match_dict = {
        "Y": y_num, 
        "M": m_num, 
        "W": w_num
    }

    # self.change = count_algorithms(self.change)
    min_pre, max_pre, avg_pre, min_post, max_post, avg_post, min_dist, max_dist, avg_dist = 0, 0 ,0, 0 ,0, 0, 0 ,0 ,0 
    overlapped_pre = [int(dist) for dist in cols[8] if dist]
    overlapped_post = [int(dist) for dist in cols[9] if dist]
    overlapped_dist = [int(dist) for dist in cols[10] if dist]

    if overlapped_pre:
        min_pre, max_pre, avg_pre = calculation_helper(overlapped_pre)
    if overlapped_post:
        min_post, max_post, avg_post = calculation_helper(overlapped_post)
    if overlapped_dist:
        min_dist, max_dist, avg_dist = calculation_helper(overlapped_dist)
    char_dist_dict = {
        "pre_dist": {"min": min_pre, "max": max_pre, "avg": avg_pre},
        "post_dist": {"min": min_post, "max": max_post, "avg": avg_post},
        "dist": {"min": min_dist, "max": max_dist, "avg": avg_dist}
    }
    
    recalls = [float(dist) for dist in cols[11]]
    precisions = [float(dist) for dist in cols[12]]
    f1s = [float(dist) for dist in cols[13]]
    avg_recall = "{:.3f}".format(sum(recalls) / len(recalls))
    avg_precision = "{:.3f}".format(sum(precisions) / len(precisions))
    avg_f1 = "{:.3f}".format(sum(f1s) / len(f1s))
    
    summarize_row = [file_type, len(f1s), "", "", "", "", "", f"{match_dict}", "", "", 
                    f"{char_dist_dict}", avg_recall, avg_precision, avg_f1]
    
    summarize_row_simplified = [m_num, y_num, avg_dist, avg_recall, avg_precision, avg_f1]

    return summarize_row, summarize_row_simplified

def process_and_write_summarization(summarize, result_csv_file):
    summarize_rows = []
    for i, (file_type, measurements) in enumerate(summarize.items()):
        cols = list(zip(*measurements))
        summarize_row, summarize_row_simplified = process(file_type, cols)
        summarize_rows.append(summarize_row_simplified)

        write_mode = "a"
        if i == 0:
            write_mode = "w"

        with open(result_csv_file, write_mode) as f:
            csv_writer = csv.writer(f)
            for row in measurements:
                csv_writer.writerow(row)
            csv_writer.writerow(summarize_row)

        with open(result_csv_file.replace(".csv", "_clean.csv"), write_mode) as f_clean:
            csv_wri = csv.writer(f_clean)
            csv_wri.writerow(summarize_row)

    return summarize.keys(), summarize_rows

def main(datasets, dataset_names, context_line_num):
    for dataset, dataset_name in zip(datasets, dataset_names):
        summarize = {}

        oracle_file = join("data", "annotation", f"{dataset}_100.json")
        measurement_file = join("data", "results", "measurement_results", dataset, f"measurement_results_metrics_{dataset}_{context_line_num}.csv")
        if context_line_num == 15:
            measurement_file = join("data", "results", "measurement_results", dataset, f"measurement_results_metrics_{dataset}.csv")
        result_dir = join("data", "results", "measurement_results", dataset, "pl_level")
        makedirs(result_dir, exist_ok=True)
        result_csv_file = join(result_dir, f"measurement_{dataset}_by_pl_{context_line_num}.csv")

        with open(measurement_file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            all_lines = [line for line in line_list if line[0]][1:] # exclude the head line

        with open(oracle_file, "r") as f:
            maps = json.load(f)

        
        for i, (oracle, measurement) in enumerate(zip(maps, all_lines)):
            source_file = oracle["mapping"]["source_file"]
            file_type = "None"
            try:
                file_type = source_file.rsplit(".", 1)[1]
            except:
                print(f"Source file with no postfix: {dataset} #{i} {source_file}")

            if file_type not in summarize.keys():
                summarize.update({file_type: [measurement]})
            else:
                summarize[file_type].append(measurement)   

        file_types , summarize_rows = process_and_write_summarization(summarize, result_csv_file)
        caption = f"Results on tracking {dataset_name} (PL-based)"
        label = f"pl_base_{dataset}"
        tex_file = join(result_dir, f"{dataset}_{context_line_num}.tex")  
        table_results_by_pl(file_types, summarize_rows, caption, label, tex_file)

def table_results_by_pl(file_types, summarize_rows, caption, label, tex_file):  
    row_names = ["Overlapping", "Exact matches", "Char. dist.", "Recall", "Precision", "F1-score"]
    col_names = file_types

    latex_table = "\\begin{table}[t]\n\\centering\n" # \\footnotesize\n
    latex_table += "\\caption{" + caption + "}\n"
    latex_table += "\\begin{tabular}{@{}" + "l" + "".join(["r"] * len(col_names)) + "@{}}\n"
    latex_table += "\\hline\n"

    latex_table += "&" + " & ".join(col_names) + " \\\\\n"
    latex_table += "\\hline\n"

    # Determine the best performance locations in each row
    summaries = list((zip(*summarize_rows)))
    for i, row_data in enumerate(summaries):
        latex_table += row_names[i] + " & " + " & ".join(map(str, row_data)) + " \\\\\n"

    latex_table += "\\hline\n"
    latex_table += "\\end{tabular}\n"
    latex_table += "\\label{tab:" + label + "}\n"
    latex_table += "\\end{table}"

    with open(tex_file, "w") as f:
        f.write(latex_table + "\n")


if __name__=="__main__":
    # separate results by programming languages, write the sepearated meta info, and table the separated results.
    # , "suppression"
    datasets = ["annotation_a", "annotation_b"]# , "annotation_b"] # the desired one or two annotated dataset(s)
    dataset_names = ["Data A", "Data B"]
    context_line_num = 15
    main(datasets, dataset_names, context_line_num)

    