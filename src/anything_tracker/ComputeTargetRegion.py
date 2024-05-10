from fast_edit_distance import edit_distance


class ComputeTargetRegion():
    def __init__(self, source_region_characters, candidate_string_lists):
        # source_region_characters and candidate_string_lists are expended strings (list)
        # expand means get the before and after contexts together
        self.source_region_characters = source_region_characters
        self.candidate_string_lists = candidate_string_lists

    def run(self):
        edit_dists = []

        for candidate_characters in self.candidate_string_lists:
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
                "target_candidate_index" : top_idx
            }
        results_set_dict["dist_based"] = metrics_based_dict
        return results_set_dict

