from anything_tracker.Line import Line
from anything_tracker.LineMap import LineMap
from anything_tracker.Hunk import Hunk


class ComputeCandidateHunks():
    def __init__(self, interest_line_range, hunk_info):
        self.interest_line_numbers_list = list(interest_line_range)
        self.base_hunk_range = hunk_info.base_hunk_range
        self.target_hunk_range = hunk_info.target_hunk_range
        self.base_hunk_source = hunk_info.base_hunk_source
        self.target_hunk_source = hunk_info.target_hunk_source
        self.base_real_changed_line_numbers = hunk_info.base_real_changed_line_numbers
        self.target_real_changed_line_numbers = hunk_info.target_real_changed_line_numbers
        self.base_real_changed_hunk_source = hunk_info.base_real_changed_hunk_source
        self.target_real_changed_hunk_source = hunk_info.target_real_changed_hunk_source
        self.diff_reported_mapped_hunk_index = hunk_info.diff_reported_mapped_hunk_index

        self.fine_grained_base_hunks = []
        self.intra_file_candidate_hunks = []
        self.single_line_maps = [] # In this file, it gets some no-change line maps.
    
    def get_fine_grained_base_hunk_and_candidate_hunks(self):
        '''
        Get real changed lines and ranges for fine_grained_base_hunk and intra_file_candidate_hunks
        Return:
         * fine_grained_base_hunk
         * intra_file_candidate_hunks
         * single_line_maps
        '''

        if self.diff_reported_mapped_hunk_index != None:
            # Otherwise, the base hunk does not includes interest element, ignore base hunk.
            # The corresponding base_hunk contains the interest element
            self.check_and_map_no_change_lines()
            if self.interest_line_numbers_list == []: 
                # All are no changed lines, and been mapped
                # No more steps needed, here the single_line_maps is the final line level map results.
                return self.fine_grained_base_hunks, self.intra_file_candidate_hunks, self.single_line_maps

            # interest_line_numbers_list updated
            # Get fine_grained_base_hunk
            is_base_consecutive = check_consecutive(self.base_real_changed_line_numbers)
            if is_base_consecutive == False:
                # Find where is the interest element in sub hunks
                self.get_sub_hunk_line_numbers_source(self.base_real_changed_line_numbers, self.base_real_changed_hunk_source, "base")

        # Get intra_file_candidate_hunks
        is_target_consecutive = check_consecutive(self.target_real_changed_line_numbers)
        if is_target_consecutive == True:
            sub_hunk = Hunk(self.target_real_changed_line_numbers, self.target_real_changed_hunk_source)
            self.intra_file_candidate_hunks.append(sub_hunk)
        else:
            self.get_sub_hunk_line_numbers_source(self.target_real_changed_line_numbers, self.target_real_changed_hunk_source, "target")

        return self.fine_grained_base_hunks, self.intra_file_candidate_hunks, self.single_line_maps

    def check_and_map_no_change_lines(self):
        target_hunk_range_to_list = list(self.target_hunk_range)

        # Get interest lines source from base_hunk
        for line_num in self.interest_line_numbers_list:
            if line_num not in self.base_real_changed_line_numbers:# In changed hunk, but not changed
                # Find the mapped line numbers in version 2
                for base_line_number, base_line_source in zip(self.base_hunk_range, self.base_hunk_source):
                    if base_line_number == line_num:
                        # interest_line = base_line_source
                        index_in_target_hunk = self.target_hunk_source.index(base_line_source)
                        target_line_number = target_hunk_range_to_list[index_in_target_hunk]
                        base_line = Line(base_line_number, base_line_source)
                        target_line = Line(target_line_number, base_line_source)
                        single_line_map_base_to_target = LineMap(base_line, target_line)
                        self.single_line_maps.append(single_line_map_base_to_target)
                        self.interest_line_numbers_list.remove(line_num)
                        break

    def get_sub_hunk_line_numbers_source(self, numbers_list, source_list, version):
        if version == "base": 
            # Append the sub hunk(s) which contain(s) the interest element to fine_grained_base_hunks
            self.get_sub_hunk_line_numbers_helper(numbers_list, source_list, [], True)
        else: # "target"
            # Update intra_file_candidate_hunks by appending sub hunks to it.
            self.get_sub_hunk_line_numbers_helper(numbers_list, source_list, self.intra_file_candidate_hunks)

    def get_sub_hunk_line_numbers_helper(self, numbers_list, source_list, sub_hunks:list, run_filter=False):
        sub_hunk_line_numbers = []
        sub_hunk_line_sources = []
        sub_hunk = []

        for i in range(len(numbers_list)):
            if numbers_list[i] != numbers_list[i-1] + 1:
                if sub_hunk:
                    sub_hunks.append(sub_hunk)
                    sub_hunk_line_numbers = []
                    sub_hunk_line_sources = []
                    sub_hunk = []
            sub_hunk_line_numbers.append(numbers_list[i])
            sub_hunk_line_sources.append(source_list[i])
            sub_hunk = Hunk(sub_hunk_line_numbers, sub_hunk_line_sources)

        if sub_hunk_line_numbers:
            sub_hunk = Hunk(sub_hunk_line_numbers, sub_hunk_line_sources)
            sub_hunks.append(sub_hunk)

        if run_filter:
            # Update fine_grained_base_hunks
            self.get_fine_grained_base_hunks(sub_hunks)

    def get_fine_grained_base_hunks(self, base_sub_hunks):
        # filter base hunks to get the ones related to interest element
        for line_num in self.interest_line_numbers_list:
            for base_sub_hunk in base_sub_hunks:
                if line_num in base_sub_hunk.line_numbers:
                    self.fine_grained_base_hunks.append(base_sub_hunk)
                    break # Get out from base_sub_hunks loop


def check_consecutive(numbers_list):
    # Return True or False
    return sorted(numbers_list) == list(range(min(numbers_list), max(numbers_list)+1))