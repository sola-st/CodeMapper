class HunkMap():
    # Hunk maps, are assign by calculating the similarities.
    def __init__(self, base_hunk: object, target_hunk: object):
        # Both base_hunk and target_hunk are an instance of class "Hunk".
        self.base_hunk = base_hunk
        self.target_hunk = target_hunk
        