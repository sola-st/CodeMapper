from fast_edit_distance import edit_distance
import numpy as np

class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_string_list, source_context=None, cnadidate_context_list=None):
        self.source_region_characters = source_region_characters
        self.candidate_string_list = candidate_string_list
        self.source_context = source_context
        self.cnadidate_context_list = cnadidate_context_list

    def compute_context_aware_similary(self):
        # Compute the necessary values
        A = np.array([1 - edit_distance(self.source_region_characters, targ) for targ in self.candidate_string_list])
        B = np.array([edit_distance(self.source_context, targ_context) for targ_context in self.cnadidate_context_list])

        best_w = 0
        best_score = -np.inf

        # Try different values of w from 0 to 1
        for w in np.linspace(1, 1, 10):
            similarity_scores = w * A + (1 - w) * B
            max_score = np.max(similarity_scores)
            if max_score > best_score:
                best_score = max_score
                best_w = w
        # print(f"Best: {best_w}")
        # Calculate similarity scores using the best w
        final_similarity_scores = best_w * A + (1 - best_w) * B
        best_index = np.argmax(final_similarity_scores)
        # best_target = self.candidate_string_list[best_index]

        # Normalize the similarity scores to [0, 1]
        min_score = np.min(final_similarity_scores)
        max_score = np.max(final_similarity_scores)
        normalized_similarity_scores = (final_similarity_scores - min_score) / (max_score - min_score)

        results_set_dict = {}
        metrics_based_dict = {
                "target_candidate_edit_distance" : float(normalized_similarity_scores[best_index]),
                "target_candidate_index" : int(best_index), 
                "region_weight": float(best_w)
            }
        results_set_dict["dist_based"] = metrics_based_dict
        return results_set_dict

    def run(self): # no context
        edit_dists = []
        if isinstance(self.source_region_characters, list):
            for source_characters, candidate_characters in zip(self.source_region_characters, self.candidate_string_list):
                if candidate_characters == None:
                    candidate_characters = ""
                dist = edit_distance(source_characters, candidate_characters)
                edit_dists.append(dist)
        else:
            for candidate_characters in self.candidate_string_list:
                if candidate_characters == None:
                    candidate_characters = ""
                dist = edit_distance(self.source_region_characters, candidate_characters)
                edit_dists.append(dist)

        # top-1 edit distance
        top_dist = min(edit_dists)
        top_idx = edit_dists.index(top_dist)
        results_set_dict = {}
        metrics_based_dict = {
                "target_candidate_edit_distance" : top_dist,
                "target_candidate_index" : top_idx,
                "region_weight": 1
            }
        results_set_dict["dist_based"] = metrics_based_dict
        return results_set_dict

