
import json
import os
from  os.path import join
from sentence_transformers import SentenceTransformer, util


class ComputeSimilarity:
    '''
    Compute similarities between source region and candidate regions
    '''
    def __init__(self, expected_region_characters:str, candidate_region_characters:list[str]):
        self.expected_region_characters = expected_region_characters
        self.candidate_region_characters = candidate_region_characters

        self.model = SentenceTransformer("data/pretrained_model")
    
    def get_top_1_similarity(self):
        # cover multiple candidates with same similarity
        selected_candidate_indices = []
        similarities = []
        highest_similarity = 0

        # expected region embedding
        if self.expected_region_characters == None or None in self.candidate_region_characters:
            pass # TODO think about how to with these cases
        else:
            expected_embedding = self.model.encode(self.expected_region_characters)
            # candidate region embedding
            for i, candidate_str in enumerate(self.candidate_region_characters):
                candidate_embedding = self.model.encode(candidate_str)
                similarity = util.cos_sim(expected_embedding, candidate_embedding)
                similarity_score = similarity.tolist()[0][0]
                if similarity_score >= highest_similarity:
                    selected_candidate_indices.append(i)
                    similarities.append(similarity_score)
                    highest_similarity = similarity_score

        return selected_candidate_indices, similarities


def get_region_characters(file):
    with open(file, "r") as f:
        data = json.load(f)
    return data

def write_source_target_pairs(pair_file, mapped_source_target_pairs):
    with open(pair_file, "w") as f:
        json.dump(mapped_source_target_pairs, f, indent=4, ensure_ascii=False)

# Read source region and candidate regions
def main():
    results_parent_dir = join("data", "results", "tracked_maps", "candidate_regions_v2")
    results = os.listdir(results_parent_dir)
    for str_i in results:
        candidate_characters = []
        results_dir = join(results_parent_dir, str_i)
        expected_file = join(results_dir, "expect.json")
        candidate_file = join(results_dir, "candidates.json")
        # always have only 1 source
        source = get_region_characters(expected_file)
        source_characters = source["source_characters"]
        # 0, 1, or more candidates
        candidates = get_region_characters(candidate_file)
        for candidate in candidates:
            candidate_characters.append(candidate["target_characters"])

        selected_candidate_indices, similarities = ComputeSimilarity(source_characters, candidate_characters).get_top_1_similarity()
        if not selected_candidate_indices or not similarities:
            continue
        pair_to_write = []
        for idx, similarity in zip(selected_candidate_indices, similarities):
            selected_candidate = candidates[idx]
            mapped_source_target_pair = {
                "source_file": source["source_file"],
                "target_file": selected_candidate["target_file"],
                "source_range": source["source_range"],
                "target_range": selected_candidate["target_range"],
                "source_characters": source_characters,
                "target_characters": selected_candidate["target_characters"],
                "kind": selected_candidate["kind"],
                "similarity" : similarity
            }
            pair_to_write.append(mapped_source_target_pair)

        pair_file = join(results_dir, "pair.json")
        write_source_target_pairs(pair_file, pair_to_write)
        print(f"Calculation for source region {str_i} is Done.")

if __name__=="__main__":
    main()