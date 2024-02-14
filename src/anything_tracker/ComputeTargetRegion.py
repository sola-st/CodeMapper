import nltk
from anything_tracker.similarity.ComputeSimilarity import ComputeSimilarity

    
def compute_highest_trade_off_score(edit_dists, bleu_scores, similarities):
    # Calculate average score for each key
    averages = []
    for dist, bleu, similarity in zip(edit_dists, bleu_scores, similarities):
        avg = (dist + bleu + similarity) / 3
        averages.append(avg)

    target_avg= max(averages)
    target_idx = averages.index(target_avg)
    return target_idx
    
class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_regions):
        self.source_region_characters = source_region_characters
        self.candidate_regions = candidate_regions

    def levenshtein_distance(self, candidate_characters):
        # step 1: compute edit distance
        # step 2: Normalizing metrics to a scale of 0 to 1
        m, n = len(self.source_region_characters), len(candidate_characters)
        matrix = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            matrix[i][0] = i
        for j in range(n + 1):
            matrix[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if self.source_region_characters[i - 1] == candidate_characters[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,      # Deletion
                    matrix[i][j - 1] + 1,      # Insertion
                    matrix[i - 1][j - 1] + cost  # Substitution
                )
        # Normalize the edit distance by dividing it by the maximum possible edit distance. 
        distance = matrix[m][n]
        return distance
        # normalized_distance = 1- distance/max(m,n)
        # return normalized_distance

    def bleu_score(self, candidate_characters):
        return nltk.translate.bleu_score.sentence_bleu([candidate_characters], self.source_region_characters)

    def compute_metrics_set(self, candidate_characters):
        dist = self.levenshtein_distance(candidate_characters)
        bleu = self.bleu_score(candidate_characters)
        return dist, bleu
    
    def get_metrics_based_dict(self, edit_dists, bleu_scores, similarities, indices, \
                keys = ["dist_based", "bleu_dist", "similarity_dist"]):
        results_set_dict = {}
        for idx, k in zip(indices, keys):
            metrics_based_dict = {
                "target_candidate" : self.candidate_regions[idx],
                "target_candidate_edit_distance" : edit_dists[idx],
                "target_candidate_bleu_score" : bleu_scores[idx],
                "target_candidate_similarity" : similarities[idx],
                "target_candidate_index" : idx
            }
            results_set_dict[k] = metrics_based_dict
        return results_set_dict

    def run(self):
        edit_dists = []
        bleu_scores = []

        candidate_region_chars = []
        for i, candidate in enumerate(self.candidate_regions):
            candidate_characters = candidate.character_sources
            candidate_region_chars.append(candidate_characters)
            if candidate_characters == None:
                candidate_characters = ""
                # TODO do not need to calculate the bleu score
            dist, bleu = self.compute_metrics_set(candidate_characters)
            edit_dists.append(dist)
            bleu_scores.append(bleu)

        # compute edit distance, bleu score and embedding similarity, respectively.
        # return 3 set of top-1 candidates.
        # [Option 1]: compute 3 different metrics ----------------
        # top-1 edit distance
        top_dist = min(edit_dists)
        top_dist_idx = edit_dists.index(top_dist)

        # top-1 bleu score
        top_bleu = max(bleu_scores)
        top_bleu_idx = bleu_scores.index(top_bleu)

        # top-1 similarity, the key of similarities_dict is ground truth index
        top_similarity_indices, top_similarities, similarities_dict = \
            ComputeSimilarity(self.source_region_characters, candidate_region_chars, 0).get_top_1_similarity()
        # if len(top_similarity_indices) == 1:
        top_similarity_idx = top_similarity_indices[0]
        indices = [top_dist_idx, top_bleu_idx, top_similarity_idx]
        similarities = similarities_dict[0]
        results_set_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, indices)

        # [Option 2]: combine the results of 3 different metrics ----------------
        average_highest_idx = compute_highest_trade_off_score(edit_dists, bleu_scores, similarities) # starts at 0.


        average_highest_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                [average_highest_idx], ["average_highest"])
        # average_highest = results_set_dict_2["average_highest"]

        # [Option 3]: check the vote to different metrics
        vote_most_dict = None
        indices_deduplicated = list(set(indices))
        if indices != indices_deduplicated:
            for idx in indices_deduplicated:
                idx_count = indices.count(idx)
                if idx_count > 1:
                    vote_most_idx = idx
                    vote_most_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                            [vote_most_idx], ["vote_most"])
                    # vote_most = results_set_dict_3["vote_most"]
                    break

        return results_set_dict, average_highest_dict, vote_most_dict