# to compare / meassure the results efficiently
def get_commit_range_pieces(commit, file_path, region_range):
    data_piece = { 
        commit: {
        "file": file_path,
        "range": region_range
        }
    }
    return data_piece