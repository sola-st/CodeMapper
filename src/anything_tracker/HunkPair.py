class HunkPair():
    def __init__(self, meta, diff_reported_mapped_hunk_index):
        self.base_hunk_range = meta.base_hunk_range
        self.target_hunk_range = meta.target_hunk_range
        self.base_hunk_source = meta.base_hunk_source
        self.target_hunk_source = meta.target_hunk_source
        self.base_real_changed_line_numbers = meta.base_real_changed_line_numbers
        self.base_real_changed_hunk_source = meta.base_real_changed_hunk_source
        self.target_real_changed_line_numbers = meta.target_real_changed_line_numbers
        self.target_real_changed_hunk_source = meta.target_real_changed_hunk_source
        self.diff_reported_mapped_hunk_index = diff_reported_mapped_hunk_index