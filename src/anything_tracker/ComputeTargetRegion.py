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
        normalized_distance = 1- distance/max(m,n)
        return distance, normalized_distance

    def bleu_score(self, candidate_characters):
        return nltk.translate.bleu_score.sentence_bleu([candidate_characters], self.source_region_characters)

    def compute_metrics_set(self, candidate_characters):
        dist, normalized_dist = self.levenshtein_distance(candidate_characters)
        bleu = self.bleu_score(candidate_characters)
        return dist, normalized_dist, bleu
    
    def get_metrics_based_dict(self, edit_dists, bleu_scores, similarities, indices, keys):
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
        normalized_dists = []
        bleu_scores = []

        candidate_region_chars = []
        for candidate in self.candidate_regions:
            candidate_characters = candidate.character_sources
            candidate_region_chars.append(candidate_characters)
            if candidate_characters == None:
                candidate_characters = ""
                # TODO do not need to calculate the bleu score
            dist, normalized_dist, bleu = self.compute_metrics_set(candidate_characters)
            edit_dists.append(dist)
            normalized_dists.append(normalized_dist)
            bleu_scores.append(bleu)

        # compute edit distance, bleu score and embedding similarity, respectively.
        # return 3 set of top-1 candidates.
        # [Option 1]: compute 3 different metrics ----------------
        # top-1 edit distance
        top_dist = min(edit_dists)
        # top_dist_indices van be one or more
        top_dist_indices = [idx for idx, dist in enumerate(edit_dists) if dist == top_dist]

        # top-1 bleu score
        top_bleu = max(bleu_scores)
        top_bleu_indices = [idx for idx, bleu in enumerate(bleu_scores) if bleu == top_bleu]

        # top-1 similarity, the key of similarities_dict is ground truth index
        top_similarity_indices, top_similarities, similarities_dict = \
            ComputeSimilarity(self.source_region_characters, candidate_region_chars, 0).get_top_1_similarity()

        # allow multiple targets for each metric
        indices = []
        indices.extend(top_dist_indices)
        indices.extend(top_bleu_indices)
        indices.extend(top_similarity_indices)
        similarities = similarities_dict[0]

        keys = []
        for i in top_dist_indices:
            keys.append("dist_based")
        for j in top_bleu_indices:
            keys.append("bleu_based")
        for k in top_similarity_indices:
            keys.append("similarity_based")

        results_set_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, indices, keys)

        # [Option 2]: combine the results of 3 different metrics ----------------
        average_highest_idx = compute_highest_trade_off_score(normalized_dists, bleu_scores, similarities) # starts at 0.
        average_highest_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                [average_highest_idx], ["average_highest"])

        # [Option 3]: check the vote to different metrics ----------------
        vote_most_dict = None
        votes = []
        indices_deduplicated = list(set(indices))
        if indices != indices_deduplicated:
            for idx in indices_deduplicated:
                idx_count = indices.count(idx)
                votes.append(idx_count)

        vote_max = min(votes)
        if votes.count(vote_max) == 1:
            vote_most_idx = indices_deduplicated[votes.index(vote_max)]
            vote_most_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                    [vote_most_idx], ["vote_most"])

        return results_set_dict, average_highest_dict, vote_most_dict