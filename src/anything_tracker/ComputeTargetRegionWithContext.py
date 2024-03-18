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
    
def levenshtein_distance(source_character, candidate_characters):
    # step 1: compute edit distance
    # step 2: Normalizing metrics to a scale of 0 to 1
    m, n = len(source_character), len(candidate_characters)
    if m == n == 0:
        return 0, 0
    
    matrix = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        matrix[i][0] = i
    for j in range(n + 1):
        matrix[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if source_character[i - 1] == candidate_characters[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # Deletion
                matrix[i][j - 1] + 1,      # Insertion
                matrix[i - 1][j - 1] + cost  # Substitution
            )
    # Normalize the edit distance by dividing it by the maximum possible edit distance. 
    distance = matrix[m][n]
    normalized_distance = 1- distance/max(m,n)
    return distance, normalized_distance

def bleu_score(source_character, candidate_characters):
    return nltk.translate.bleu_score.sentence_bleu([candidate_characters], source_character)

def value_weight(pre, chars, post):
    return (chars + (pre + post) / 2) / 2

class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_string_lists):
        # source_region_characters and candidate_string_lists are expended strings (list)
        # expand means get the before and after contexts together
        self.source_region_characters = source_region_characters
        self.candidate_string_lists = candidate_string_lists

    def compute_metrics_set(self, source_characters, candidate_characters):
        dist, normalized_dist = levenshtein_distance(source_characters, candidate_characters)
        bleu = bleu_score(source_characters, candidate_characters)
        return dist, normalized_dist, bleu
    
    def get_metrics_based_dict(self, edit_dists, bleu_scores, similarities, indices, keys):
        results_set_dict = {}
        for idx, k in zip(indices, keys):
            metrics_based_dict = {
                "idx": idx,
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

        pre_str_list = []
        candidate_str_list = []
        post_str_list = []

        source_pre, source_characters, source_post = self.source_region_characters
        for candidate_strs_list in self.candidate_string_lists:
            for candidate in self.source_region_characters, candidate_strs_list:
                candidate_pre, candidate_characters, candidate_post = candidate
                if candidate_characters == None:
                    candidate_characters = ""
                pre_str_list.append(candidate_pre)
                candidate_str_list.append(candidate_characters)
                post_str_list.append(candidate_post)

                pre_dist, pre_normalized_dist, pre_bleu = self.compute_metrics_set(source_pre, candidate_pre)
                dist, normalized_dist, bleu = self.compute_metrics_set(source_characters, candidate_characters)
                post_dist, post_normalized_dist, post_bleu = self.compute_metrics_set(source_post, candidate_post)
                dist = value_weight(pre_dist, dist, post_dist)
                normalized_dist = value_weight(pre_normalized_dist, normalized_dist, post_normalized_dist)
                bleu = value_weight(pre_bleu, bleu, post_bleu)
           
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
        pre_top_similarity_indices, pre_top_similarities, pre_similarities_dict = \
                ComputeSimilarity(source_pre, pre_str_list, 0).get_top_1_similarity()
        top_similarity_indices, top_similarities, similarities_dict = \
                ComputeSimilarity(source_characters, candidate_str_list, 0).get_top_1_similarity()
        post_top_similarity_indices, post_top_similarities, post_similarities_dict = \
                ComputeSimilarity(source_post, post_str_list, 0).get_top_1_similarity()
        
        # similarities = similarities_dict[0] # all similarities
        similarities = []
        tmp_pre = pre_similarities_dict[0]
        tmp = similarities_dict[0]
        tmp_post = post_similarities_dict[0]
        for pre, char, post in zip(tmp_pre, tmp, tmp_post):
            similarity = value_weight(pre, char, post)
            similarities.append(similarity)

        # always pick the top-1, it should comes from git diff
        unique_indices = []
        unique_indices.append(top_dist_indices[0])
        unique_indices.append(top_bleu_indices[0])
        unique_indices.append(similarities.index(max(similarities)))

        keys = ["dist_based", "bleu_based", "similarity_based"]
        results_set_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, unique_indices, keys)

        # [Option 2]: combine the results of 3 different metrics ----------------
        average_highest_idx = compute_highest_trade_off_score(normalized_dists, bleu_scores, similarities) # starts at 0.
        average_highest_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                [average_highest_idx], ["average_highest"])

        # [Option 3]: check the vote to different metrics ----------------
        vote_most_dict = None
        votes = []
        indices = []
        indices.extend(top_dist_indices)
        indices.extend(top_bleu_indices)
        indices.extend(top_similarity_indices)

        indices_deduplicated = list(set(indices))
        if indices != indices_deduplicated:
            for idx in indices_deduplicated:
                idx_count = indices.count(idx)
                votes.append(idx_count)

            vote_max = max(votes)
            if votes.count(vote_max) == 1:
                vote_most_idx = indices_deduplicated[votes.index(vote_max)]
                vote_most_dict = self.get_metrics_based_dict(edit_dists, bleu_scores, similarities, 
                        [vote_most_idx], ["vote_most"])

        return results_set_dict, average_highest_dict, vote_most_dict