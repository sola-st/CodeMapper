import json
import os
from os.path import join
from anything_tracker.experiments.TrackHistoryPairs import get_category_subfolder_info


class HistoryPairCount():
    def __init__(self, oracle_history_parent_folder, result_count_file):
        self.oracle_history_parent_folder = oracle_history_parent_folder
        self.result_count_file = result_count_file

        self.row_names = [] # program element names
        self.counts = []

    def generate_table(self):
        # get table contents
        self.row_names.append("Total")
        elements = sum([c[0] for c in self.counts])
        histories = sum([c[1] for c in self.counts])
        self.counts.append([elements, histories])
        col_names = ["Program element", "Histories"] 
        caption = "Number of Java program element histories"
        label = "number_java_element_data"

        # start to write table
        latex_table = "\\begin{table}[htbp]\n\\centering\n"
        latex_table += "\\caption{" + caption + "}\n"
        latex_table += "\\begin{tabular}{" + "l" + "".join(["r"] * (len(col_names))) + "}\n"
        latex_table += "\\hline\n"

        latex_table += "& " + " & ".join(col_names) + " \\\\\n"
        latex_table += "\\hline\n"

        data_len = len(self.counts)
        for i, count in enumerate(self.counts):
            latex_table += self.row_names[i] + " & " + " & ".join(map(str,count)) + " \\\\\n"
            if i + 2 == data_len:
                latex_table += "\\hline\n"

        latex_table += "\\hline\n"
        latex_table += "\\end{tabular}\n"
        latex_table += "\\label{tab:" + label + "}\n"
        latex_table += "\\end{table}"

        with open(self.result_count_file, "w") as f:
            f.write(latex_table + "\n")

    def run(self):
        category_subset_pairs = get_category_subfolder_info(oracle_history_parent_folder)
        pre_category = None
        element_level_count = 0
        element_level_subfolder_count = 0

        for category, subset in category_subset_pairs: # eg., method, test
            if pre_category != category:
                self.row_names.append(category)
                pre_category = category
                if element_level_count > 0 :
                    self.counts.append([element_level_subfolder_count, element_level_count])
                    element_level_subfolder_count = 0
                    element_level_count = 0

            subset_level_count = 0
            subset_folder = join(oracle_history_parent_folder, category, subset)
            subset_folder_len = len(os.listdir(subset_folder))
            for num_folder in range(subset_folder_len):
                num_folder_str = str(num_folder)
                history_file_path = join(oracle_history_parent_folder, category, subset,\
                        num_folder_str, "expect_full_histories.json")

                with open(history_file_path) as f:
                    histories_pairs = json.load(f)
                minus = 0
                for meta in histories_pairs:
                    if meta["target_range"] == "None":
                        minus += 1
                        continue
                    character_range_list = json.loads(meta["target_range"])
                    if not character_range_list or \
                        (character_range_list[1] == character_range_list[3]) and (character_range_list[0] == character_range_list[2]):
                        minus += 1

                subset_level_count += (len(histories_pairs) - minus)
            
            element_level_count += subset_level_count
            element_level_subfolder_count += subset_folder_len

        self.counts.append([element_level_subfolder_count, element_level_count])
        
        self.generate_table()

if __name__ == "__main__":
    result_count_file = join("data", "results", "analysis_on_codetracker_data", "java_history_counts.tex")
    oracle_history_parent_folder = join("data", "converted_data")
    HistoryPairCount(oracle_history_parent_folder, result_count_file).run()