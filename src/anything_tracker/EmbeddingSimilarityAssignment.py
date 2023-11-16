from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.optimize import linear_sum_assignment
from anything_tracker.CommmonFunctions import all_elements_to_maps

from anything_tracker.LineMap import LineMap


class EmbeddingSimilarityAssignment:
    def __init__(
        self,
        base_real_changed_hunk_source,
        target_real_changed_hunk_source,
        base_real_changed_line_numbers,
        target_real_changed_line_numbers
    ):
        self.base_real_changed_hunk_source = base_real_changed_hunk_source
        self.target_real_changed_hunk_source = target_real_changed_hunk_source
        self.base_real_changed_line_numbers = base_real_changed_line_numbers
        self.target_real_changed_line_numbers = target_real_changed_line_numbers
        self.model = SentenceTransformer("data/pretrained_model")

        self.hungarian_line_maps = []
        # a list to store all the calculated similarities, each element is a list for single line.
        self.base_line_level_similarity_matrix = []

    def get_embeddings(self, hunk):
        embedding_list = []
        for line in hunk:
            line_embedding = self.model.encode(line)
            embedding_list.append(line_embedding)
        return embedding_list

    def get_line_level_similarity_matrix(self):
        base_line_embedding_list = self.get_embeddings(self.base_real_changed_hunk_source)
        target_line_embedding_list = self.get_embeddings(self.target_real_changed_hunk_source)

        for base_embedding in base_line_embedding_list:
            current_line_similarities = []
            for target_embedding in zip(target_line_embedding_list):
                similarity = util.cos_sim(base_embedding, target_embedding)
                current_line_similarities.append(similarity.tolist()[0][0])
            self.base_line_level_similarity_matrix.append(current_line_similarities)

    def hungarian_assignment(self):
        similarity_matrix = np.array(self.base_line_level_similarity_matrix)
        # Convert similarity values to costs (negative similarity)
        similarity_matrix = -similarity_matrix

        # Solve the assignment problem
        row_indices, col_indices = linear_sum_assignment(similarity_matrix)

        base_line_number_copy = self.base_real_changed_line_numbers.copy()
        base_line_source_copy = self.base_real_changed_hunk_source.copy()

        for row_idx, col_idx in zip(row_indices, col_indices):
            base_real_changed_line_number = self.base_real_changed_line_numbers[row_idx]
            base_line_source = self.base_real_changed_hunk_source[row_idx]
            target_real_changed_line_number = self.target_real_changed_line_numbers[col_idx]
            target_line_source = self.target_real_changed_hunk_source[col_idx]
            hungarian_line_map = LineMap(base_real_changed_line_number, base_line_source, \
                target_real_changed_line_number, target_line_source)
            self.hungarian_line_maps.append(hungarian_line_map)

            base_line_number_copy.remove(base_real_changed_line_number)
            base_line_source_copy.remove(base_line_source)
        
        if base_line_number_copy:
            deleted_line_maps = all_elements_to_maps(base_line_number_copy, base_line_source_copy, "base")
            self.hungarian_line_maps.extend(deleted_line_maps)

        return self.hungarian_line_maps