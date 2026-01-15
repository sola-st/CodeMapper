import csv
from os.path import join, exists
from matplotlib import pyplot as plt

def get_f1s(file_list):
    f1s = []
    for file in file_list:
        with open(file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)
            # include the outliers, like file path not match
            all_match_results = [line[6] for line in line_list if line]
            all = len(all_match_results) -2 # 1 head, 1 summary
            summary_line = line_list[-1]
            tmp = [s for s in summary_line if s]
            if len(tmp) < 2:
                summary_line = line_list[-2][7:]
                all -= 1
            else:
                summary_line = summary_line[7:]
        # summary should be [YMW, pre character distance, post, all, recall, precision, f1, note]
        summary = [s for s in summary_line if s] 
        f1s.append(float(summary[4] ))
    return f1s

def plot_f1_scores(f1s, labels, context_lines, result_pdf):
    colors = ["#DE3163", "#2973B2", "#493D9E", "#0F828C", "#E53888", "#FF9B45" ]
    markers = ["o", "s", "^", "|", "|", "|"]
    
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams.update({'font.size': 10})
    plt.subplots(figsize=(5.3, 3))
    for f1_list, label, marker, color in zip(f1s, labels, markers, colors):
        plt.plot(context_lines, f1_list, marker=marker, label=label, color=color)

    indices = [i for i, num in enumerate(context_lines) if num in [0, 5, 15, 30]]
    avoid_overlapping = [i for i, num in enumerate(context_lines) if num in [5, 15, 30]]
    for i in indices:  
        for j, (f1_list, color) in enumerate(zip(f1s, colors)): 
            if i in avoid_overlapping and j == 1:
                # avoid dispaly overlapping
                plt.text(context_lines[i], f1_list[i], str(f1_list[i]), va='top', ha='left', color=color)
            else:
                plt.text(context_lines[i], f1_list[i], str(f1_list[i]), va='bottom', ha='left', color=color)

    plt.xlim(0, 34)
    plt.ylim(0.5, 1)
    plt.xlabel('Context size')
    plt.ylabel('F1-sorce')
    plt.grid()
    plt.tight_layout(pad=0)
    plt.legend(loc='lower right')
    plt.savefig(result_pdf)
    print(f"* Generate plot: {result_pdf}")


if __name__=="__main__":
    common_folder = join("data", "results", "measurement_results")
    output_dir = join("data", "results", "table_plots")
    default_context_line = 15
    context_lines = [0, 1, 2, 3, 5, 10, 15, 20, 25, 30]
    datasets = ["annotation_a", "annotation_b", "suppression", "variable_test", "method_test", "block_test"]

    overall_f1s = []
    overall_labels = []
    for dataset in datasets:
        common = join(common_folder, dataset)
        file_base = join(common, f"measurement_results_metrics_{dataset}")
        file_list = []
        for context_line in context_lines:
            if context_line == default_context_line:
                tmp = f"{file_base}.csv"
                approach_file = tmp if exists(tmp) else f"{file_base}_15.csv"
                file_list.append(approach_file)
            elif context_line == 0:
                file = f"{file_base}_off_context.csv"
                if exists(file):
                    file_list.append(file)
                else:
                    file_list.append(f"{file_base}_{context_line}.csv")
            else:
                file_list.append(f"{file_base}_{context_line}.csv")
        f1s = get_f1s(file_list)
        overall_f1s.append(f1s)

    labels = ["Annotated data A", "Annotated data B", "Suppression data", "Variable", "Method", "Block"]
    result_pdf = join("data", "results", "table_plots", "ablation_context_sizes_f1_all.pdf")
    plot_f1_scores(overall_f1s, labels, context_lines, result_pdf)
