import argparse
import json
from  os.path import join
from sentence_transformers import SentenceTransformer, util

parser = argparse.ArgumentParser(description="Compute similarity between expected region and candidate regions.")
parser.add_argument("--results_dir", help="Directory to put the results", required=True)


class ComputeSimilarity:
    '''
    Compute similarities between expect region and candidate regions
    '''
    def __init__(self, expected_region_characters:str, candidate_region_characters:list[str], ground_truth_index):
        self.expected_region_characters = expected_region_characters
        self.candidate_region_characters = candidate_region_characters
        self.ground_truth_index = int(ground_truth_index)

        self.model = SentenceTransformer("data/pretrained_model")
    
    def get_top_1_similarity(self):
        # cover multiple candidates with same similarity
        selected_candidate_indices = []
        similarities = [] # highest
        ground_truth_level_similarities = []
        highest_similarity = 0

        # expected region embedding
        if self.expected_region_characters == None:
            self.expected_region_characters = ""

        expected_embedding = self.model.encode(self.expected_region_characters)
        # candidate region embedding
        for i, candidate_str in enumerate(self.candidate_region_characters):
            formatted_similarity_score = 0
            if candidate_str == None:
                candidate_str = ""
            candidate_embedding = self.model.encode(candidate_str)
            similarity = util.cos_sim(expected_embedding, candidate_embedding)
            similarity_score = similarity.tolist()[0][0]
            formatted_similarity_score = round(similarity_score, 4)
            ground_truth_level_similarities.append(formatted_similarity_score)
            if similarity_score >= highest_similarity:
                selected_candidate_indices.append(i)
                similarities.append(formatted_similarity_score)
                highest_similarity = similarity_score
        
        ground_truth_level_similarities_dict = {self.ground_truth_index : ground_truth_level_similarities}

        return selected_candidate_indices, similarities, ground_truth_level_similarities_dict
    

def get_region_characters(file):
    with open(file, "r") as f:
        data = json.load(f)
    return data

def write_source_target_pairs(pair_file, mapped_source_target_pairs):
    with open(pair_file, "w") as f:
        json.dump(mapped_source_target_pairs, f, indent=4, ensure_ascii=False)

def main(results_dir):
    candidate_characters = []
    # source
    source_file = join(results_dir, "source.json")
    source = get_region_characters(source_file)

    # expect: always have only 1 expected result
    expected_file = join(results_dir, "expect.json")
    expect = get_region_characters(expected_file)
    expected_characters = expect["expected_characters"]

    # predict: 0, 1, or more candidates
    candidate_file = join(results_dir, "candidates.json")
    candidates = get_region_characters(candidate_file)
    for candidate in candidates:
        candidate_characters.append(candidate["target_characters"])

    ground_truth_index = results_dir.split("/")[-1]
    # compute similarity between expected and predicted
    selected_candidate_indices, similarities, ground_truth_level_similarities_dict = \
            ComputeSimilarity(expected_characters, candidate_characters, ground_truth_index).get_top_1_similarity()

    pair_to_write = []
    for idx, similarity in zip(selected_candidate_indices, similarities):
        mapped_source_target_pair = {
            "source_file": source["source_file"],
            "expected_file": expect["expected_file"],
            "predicted_file": None,
            "source_range": source["source_range"],
            "expected_range": expect["expected_range"],
            "predicted_range": None,
            "source_characters": source["source_characters"],
            "expected_characters": expected_characters,
            "predicted_characters": None,
            "kind": None,
            "similarity" : similarity
        }
        if isinstance(idx, int):
            selected_candidate = candidates[idx]
            mapped_source_target_pair["predicted_file"] = selected_candidate["target_file"]
            predict_range = selected_candidate["target_range"]
            if predict_range == "[0, 0, 0, 0]":
                predict_range = None
            mapped_source_target_pair["predicted_range"] = predict_range
            mapped_source_target_pair["predicted_characters"] = selected_candidate["target_characters"]
            mapped_source_target_pair["kind"] = selected_candidate["kind"]

        pair_to_write.append(mapped_source_target_pair)

    pair_file = join(results_dir, "pair.json")
    write_source_target_pairs(pair_file, pair_to_write)
    print(f"Calculation for expect region {ground_truth_index} is Done.")

    return ground_truth_level_similarities_dict

if __name__=="__main__":
    args = parser.parse_args()
    main(args.results_dir)