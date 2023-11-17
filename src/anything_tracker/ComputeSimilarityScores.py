from sentence_transformers import SentenceTransformer, util
import numpy as np
from scipy.optimize import linear_sum_assignment
from anything_tracker.CommonFunctions import all_elements_to_hunk_maps, all_elements_to_line_maps
from anything_tracker.HunkMap import HunkMap
from anything_tracker.LineMap import LineMap


class ComputeSimilarityScores:
    '''
    Computer similarity matrices and assign the mappings:
     * Hunk level, to calculate the similarity scores for candidate hunks --> Get the top-1 mapped hunk
     * Line level, to calculate the line similarities between base hunk and its corresponding top-1 mapped hunk
    '''
    def __init__(self, fine_grained_base_hunks, intra_file_candidate_hunks):
        self.fine_grained_base_hunks = fine_grained_base_hunks
        self.intra_file_candidate_hunks = intra_file_candidate_hunks

        self.model = SentenceTransformer("data/pretrained_model")

        self.hunk_level_similarity_matrix = []
        self.hungarian_hunk_maps = []

        # After getting the hungarian_hunk_maps,
        # calculate the line similarities inside the mapped hunks
        # The hungarian_hunk_maps can have more than 1 hunk maps.
        # hungarian_line_maps is a lis of single hunk hungarian_line_maps
        self.line_level_similarity_matrix = []
        self.hungarian_line_maps = []
    
    # Hunk level part start.
    def get_hunk_embeddings(self, hunk_list):
        embedding_list = []
        for hunk in hunk_list:
            hunk_embedding = self.model.encode(hunk.line_sources)
            embedding_list.append(hunk_embedding)
        return embedding_list

    def get_hunk_level_similarity_matrix(self):
        base_hunk_embedding_list = self.get_hunk_embeddings(self.fine_grained_base_hunks)
        target_candidate_hunk_embedding_list = self.get_hunk_embeddings(self.intra_file_candidate_hunks)

        for base_hunk_embedding in base_hunk_embedding_list:
            current_hunk_similarities = []
            for target_candidate_hunk_embedding in target_candidate_hunk_embedding_list:
                similarity = util.cos_sim(base_hunk_embedding, target_candidate_hunk_embedding)
                current_hunk_similarities.append(similarity.tolist()[0][0])
            self.hunk_level_similarity_matrix.append(current_hunk_similarities)
    
    # Solve the assignment problem at hunk level.
    def hungarian_assignment_hunk_level(self):
        self.get_hunk_level_similarity_matrix()
        similarity_matrix = np.array(self.hunk_level_similarity_matrix)
        # Convert similarity values to costs (negative similarity)
        similarity_matrix = -similarity_matrix

        row_indices, col_indices = linear_sum_assignment(similarity_matrix)
        base_hunk_copy = self.fine_grained_base_hunks.copy()

        for row_idx, col_idx in zip(row_indices, col_indices):
            base_hunk = self.fine_grained_base_hunks[row_idx]
            target_candidate_hunk = self.intra_file_candidate_hunks[col_idx]
            hungarian_hunk_map = HunkMap(base_hunk, target_candidate_hunk)
            self.hungarian_hunk_maps.append(hungarian_hunk_map)
            base_hunk_copy.remove(base_hunk)
        
        if base_hunk_copy:
            # TODO check if the self.intra_file_candidate_hunks includes cross file hunks
            # if yes: The hunk is deleted.
            deleted_or_added_hunk_maps = all_elements_to_hunk_maps(base_hunk_copy, None, "base")
            self.hungarian_hunk_maps.extend(deleted_or_added_hunk_maps)

        return self.hungarian_hunk_maps
    # Hunk level part end.
       
    # Line level part start.
    def get_line_embeddings(self, hunk):
        embedding_list = []
        for line in hunk:
            line_embedding = self.model.encode(line)
            embedding_list.append(line_embedding)
        return embedding_list
    
    def get_line_level_similarity_matrix(self):
        for hunk_map in self.hungarian_hunk_maps:
            single_hunk_line_level_similarity_matrix = []
            base_line_embedding_list = self.get_line_embeddings(hunk_map.base_hunk.line_sources)
            target_line_embedding_list = self.get_line_embeddings(hunk_map.target_hunk.line_sources)

            for base_embedding in base_line_embedding_list:
                current_line_similarities = []
                for target_candidate_embedding in target_line_embedding_list:
                    similarity = util.cos_sim(base_embedding, target_candidate_embedding)
                    current_line_similarities.append(similarity.tolist()[0][0])
                single_hunk_line_level_similarity_matrix.append(current_line_similarities)

            self.line_level_similarity_matrix.append(single_hunk_line_level_similarity_matrix)
            
    # Solve the assignment problem at line level.
    def hungarian_assignment_line_level(self):
        self.get_line_level_similarity_matrix()
        for line_similarity_matrix, hunk_map in zip(self.line_level_similarity_matrix, self.hungarian_hunk_maps):
            similarity_matrix = np.array(line_similarity_matrix)
            similarity_matrix = -similarity_matrix

            row_indices, col_indices = linear_sum_assignment(similarity_matrix)
            base_lines = hunk_map.base_hunk.lines # line number and line source
            base_lines_copy = base_lines.copy()
            target_lines = hunk_map.target_hunk.lines

            for row_idx, col_idx in zip(row_indices, col_indices):
                base_line = base_lines[row_idx]
                target_line = target_lines[col_idx]

                hungarian_line_map = LineMap(base_line, target_line)
                self.hungarian_line_maps.append(hungarian_line_map)
                base_lines_copy.remove(base_line)
            
            if base_lines_copy:
                deleted_or_added_line_maps = all_elements_to_line_maps(base_lines_copy, None, "base")
                self.hungarian_line_maps.extend(deleted_or_added_line_maps)

        return self.hungarian_line_maps
    # Line level part end.

