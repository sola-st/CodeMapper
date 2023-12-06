import csv
from multiprocessing import Pool, cpu_count
import os
from os.path import join
from anything_tracker.similarity.ComputeSimilarity import main as compute_similarity


"""
Computes similarity for all the candidate regions.
Get the region with highest similarity score, 
write source-expected-predicted pairs to a JSON file.
"""

def add_similarity_to_measurement_csv_file(similarities_to_add:list):
    similarities_to_add.insert(0, "Embedding similarity")
    measurement_csv_file = join("data", "results", "measurement_results.csv")
    with open(measurement_csv_file, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)

    for row, similarity in zip(rows, similarities_to_add):
        row.append(similarity)

    with open(measurement_csv_file, "w") as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def run():
    args_results_dir = []
    all_similarities = []

    results_parent_dir = join("data", "results", "tracked_maps", "candidate_regions")
    results = os.listdir(results_parent_dir)
    for str_i in results:
        results_dir = join(results_parent_dir, str_i)
        args_results_dir.append(results_dir)
    
    cores_to_use = cpu_count() - 1
    cores_to_use = 1
    print(f"Using {cores_to_use} cores in parallel.")
    with Pool(processes=cores_to_use) as pool:
        async_results = [pool.apply_async(compute_similarity, (item,)) for item in args_results_dir]
        ground_truth_level_similarities = [async_result.get() for async_result in async_results]
    
    sorted_similarities = sorted(ground_truth_level_similarities, key=lambda d: list(d.keys()))
    for similarities in sorted_similarities:
        for key, val in similarities.items():
            all_similarities.extend(val)

    # add similarity to the results csv file
    add_similarity_to_measurement_csv_file(all_similarities)

        
if __name__ == "__main__":
    run()