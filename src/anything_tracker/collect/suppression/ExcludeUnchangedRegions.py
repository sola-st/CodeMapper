import csv
import os
from os.path import join
import shutil


def repo_name_to_git_url():
    repo_file = join("data", "python_repos.txt")
    with open(repo_file) as f:
        git_urls = f.read().splitlines()

    repo_names = []
    for git_url in git_urls:
        repo_name = git_url.split("/")[-1].replace(".git", "")
        repo_names.append(repo_name)
    return repo_names


class ExcludeUnchangedRegions():
    def __init__(self, measurement_file, base_oracle_folder, new_oracle_folder, idx_mapping_file):
        self.measurement_file = measurement_file # here we use the one line level diff
        self.base_oracle_folder = base_oracle_folder # oracle with the unchanged regions
        self.new_oracle_folder = new_oracle_folder
        self.idx_mapping_file = idx_mapping_file
        # records the mappings between the numfolders, 
        # e.g., the idx5 in base is the idx1 in new, [repo_name, 5, 1] 
        self.idx_mappings = [] 
        self.repo_names = repo_name_to_git_url()

    def get_unchanged_info(self):
        with open(self.measurement_file, "r") as f:
            csv_reader = csv.reader(f)
            line_list = list(csv_reader)

        # get the indices where the change operation is "diff_no_change"
        # 1: is used to exclude the header.
        ground_truth_indices = [line[0] for line in line_list if line and line[0]][1:]
        change_operations = [line[4] for line in line_list if line][1:-1]
        assert len(ground_truth_indices) == len(change_operations)
        return ground_truth_indices, change_operations

    def run(self):
        ground_truth_indices, change_operations = self.get_unchanged_info()
        # group and remove the unchanges for each repo
        current_repo_name = None
        indices_to_exclude = []
        for idx, operation in zip(ground_truth_indices, change_operations):
            if idx.isnumeric() == False: # it includes the repo_name
                if indices_to_exclude:
                    self.remove_the_unchanges(current_repo_name, indices_to_exclude)
                    # go for the next repo
                    indices_to_exclude = [] 
                current_repo_name, idx = idx.split(" - ")
            if "DIFF_NO_CHANGE" in operation:
                indices_to_exclude.append(idx)

        # for the last repo
        if indices_to_exclude:
            self.remove_the_unchanges(current_repo_name, indices_to_exclude)

        self.write_mappings() # only for those have unchanged regions

        # copy oracles for the other repos (originally without unchanges)
        for repo_name in self.repo_names:
            shutil.copytree(join(self.base_oracle_folder, repo_name), join(self.new_oracle_folder, repo_name))
            
    def remove_the_unchanges(self, repo_name, indices_to_exclude):
        self.repo_names.remove(repo_name)
        repo_base_oracle_dir = join(self.base_oracle_folder, repo_name)
        numfolders = os.listdir(repo_base_oracle_dir)
        new_idx = 0
        for nf in numfolders:
            if not nf in indices_to_exclude:
                self.idx_mappings.append([repo_name, nf, new_idx])
                shutil.copytree(join(repo_base_oracle_dir, nf), join(self.new_oracle_folder, repo_name, str(new_idx)))
                new_idx += 1

    def write_mappings(self):
        with open(self.idx_mapping_file, "w") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(self.idx_mappings)


if __name__=="__main__":
    measurement_file = join("data", "results", "measurement_results", \
                            "suppression", "measurement_results_metrics_suppression_line.csv")
    base_oracle_folder = join("data", "suppression_data_with_unchanges")
    new_oracle_folder = join("data", "suppression_data")
    os.makedirs(new_oracle_folder, exist_ok=True)
    idx_mapping_file = join(new_oracle_folder, "idx_mappings_wo_unchanges.csv")
    ExcludeUnchangedRegions(measurement_file, base_oracle_folder, new_oracle_folder, idx_mapping_file).run()