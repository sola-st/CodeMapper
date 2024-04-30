from anything_tracker.similarity.ComputeSimilarity import ComputeSimilarity

    
class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_string_lists):
        # source_region_characters and candidate_string_lists are expended strings (list)
        # expand means get the before and after contexts together
        self.source_region_characters = source_region_characters
        self.candidate_string_lists = candidate_string_lists

    def levenshtein_distance(self, candidate_characters):
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
        distance = matrix[m][n]
        normalized_distance = 1- distance/max(m,n)
        return normalized_distance
        # TODO change the return value type as needed
    

    def run(self):
        edit_dists = []

        for candidate_characters in self.candidate_string_lists:
            if candidate_characters == None:
                candidate_characters = ""
            dist = self.levenshtein_distance(candidate_characters)
            edit_dists.append(dist)

        # top-1 edit distance
        top_dist = min(edit_dists)
        top_idx = edit_dists.index(top_dist)
        results_set_dict = {}
        metrics_based_dict = {
                "idx": top_idx,
                "target_candidate_edit_distance" : top_dist,
                "target_candidate_index" : top_idx
            }
        results_set_dict["dist_based"] = metrics_based_dict
        return results_set_dict

