import nltk

    
def compute_highest_trade_off_score(edit_dists, bleu_scores):
    # Calculate average score for each key
    averages = {}
    for key in edit_dists.keys():
        averages[key] = (bleu_scores[key] - edit_dists[key]) / 2
    # Find the key with the highest average score
    max_key = max(averages, key=averages.get)
    # max_score = averages[max_key]
    return max_key
    
class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_regions):
        self.source_region_characters = source_region_characters
        self.candidate_regions = candidate_regions

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
        return matrix[m][n]

    def bleu_score(self, candidate_characters):
        return nltk.translate.bleu_score.sentence_bleu([candidate_characters], self.source_region_characters)

    def compute_metrics_set(self, candidate_characters):
        dist = self.levenshtein_distance(candidate_characters)
        bleu = self.bleu_score(candidate_characters)
        return dist, bleu

    def run(self):
        edit_dists:dict = {}
        bleu_scores:dict = {}
        target_candidate = None

        for i, candidate in enumerate(self.candidate_regions):
            candidate_characters = candidate.character_sources
            if candidate_characters == None:
                candidate_characters = ""
            dist, bleu = self.compute_metrics_set(candidate_characters)
            edit_dists[i] = dist
            bleu_scores[i] = bleu
        top_1_candidate_index = compute_highest_trade_off_score(edit_dists, bleu_scores) # starts st 0.

        target_candidate = self.candidate_regions[top_1_candidate_index]
        target_candidate_edit_distance = edit_dists[top_1_candidate_index]
        target_candidate_bleu_score= bleu_scores[top_1_candidate_index]

        return target_candidate, target_candidate_edit_distance, target_candidate_bleu_score