from anything_tracker.CommmonFunctions import all_elements_to_maps
from anything_tracker.EmbeddingSimilarityAssignment import EmbeddingSimilarityAssignment
from anything_tracker.LineMap import LineMap


class GetSingleLineMaps():
    def __init__(self, interest_line_range, hunk_info):
        self.interest_line_numbers_list = list(interest_line_range)
        # hunk_info received from GitDiffToTargetChangedHunk.py.
        self.base_hunk_range = hunk_info["base_hunk_range"]
        self.target_hunk_range = hunk_info["target_hunk_range"]
        self.base_hunk_source = hunk_info["base_hunk_source"]
        self.target_hunk_source = hunk_info["target_hunk_source"]
        self.base_real_changed_line_numbers = hunk_info["base_real_changed_line_numbers"]
        self.target_real_changed_line_numbers = hunk_info["target_real_changed_line_numbers"]
        self.base_real_changed_hunk_source = hunk_info["base_real_changed_hunk_source"]
        self.target_real_changed_hunk_source = hunk_info["target_real_changed_hunk_source"]

        self.single_line_maps = []

    def further_process_target_change_hunk(self):
        '''
        Scenario 1: interest element is changed. 
            1.1: single line hunk -> single line map.
            1.2: multi-line hunk -> similarity check
        Scenario 2: interest element is not changed, and not in changed hunk sources.
        Scenario 3: interest element is not changed, but appears in changed hunks. 
                (Covered in following check_whether_line_real_changed)
        For example:
            diff --git a/greeting.py b/greeting.py
            index 9b3818d..16cb5ec 100644
            --- a/greeting.py
            +++ b/greeting.py
            @@ -8,9 +8,8 @@ def main():
                person = "Alice"
                greeting = greet(person)
            
            -    message = "this is a test"
                # pylint: disable=unused-variable
            -    capitalized_message = capitalize_string(message)
            +    capitalized_message = capitalize_string(greeting)
            
                print(greeting)
                print(capitalized_message)
        
        The lines in changed hunk, but with no "-" or "+" symbol, also not changed, but line numbers may changed.
        '''
        
        all_no_change_mark = False
        if self.target_hunk_range != "":
            # Scenario 3
            all_no_change_mark = self.check_whether_line_real_changed()
            print("3")
            if all_no_change_mark == False:
                base_len = len(self.base_real_changed_line_numbers)
                target_len = len(self.target_real_changed_line_numbers)
                # here the base and target will not be empty at the same time
                if  base_len == 0: # no lines deleted
                    added_line_maps = all_elements_to_maps(self.target_real_changed_line_numbers, self.target_real_changed_hunk_source, "target")
                    self.single_line_maps.extend(added_line_maps)
                elif target_len == 0:
                    deleted_line_maps = all_elements_to_maps(self.base_real_changed_line_numbers, self.base_real_changed_hunk_source, "base")
                    self.single_line_maps.extend(deleted_line_maps)
                elif base_len == target_len == 1: # Scenario 1.1
                    single_line_hunk_maps = LineMap(self.base_real_changed_line_numbers[0], self.base_real_changed_hunk_source[0], \
                            self.target_real_changed_line_numbers[0], self.target_real_changed_hunk_source[0])
                    self.single_line_maps.append(single_line_hunk_maps)
                else: # Scenario 1.2, multi-line hunk maps, need to check similarities
                    print("1.2")
                    embedding_similarity = EmbeddingSimilarityAssignment(self.base_real_changed_hunk_source, \
                            self.target_real_changed_hunk_source, \
                            self.base_real_changed_line_numbers, self.target_real_changed_line_numbers)
                    embedding_similarity.get_line_level_similarity_matrix()
                    hungarian_line_maps = embedding_similarity.hungarian_assignment()
                    self.single_line_maps.extend(hungarian_line_maps)
        else:
            # Scenario 4: interest element not changed
            print("4, LocateNoChange")

        return self.single_line_maps

    def check_whether_line_real_changed(self):
        target_hunk_range_to_list = list(self.target_hunk_range)
        all_no_change_mark = False

        # get interest lines source from base_hunk
        for line_num in self.interest_line_numbers_list:
            if line_num not in self.base_real_changed_line_numbers:
                for base_line_number, base_line in zip(self.base_hunk_range, self.base_hunk_source):
                    if base_line_number == line_num:
                        # interest_line = base_line
                        index_in_target_hunk = self.target_hunk_source.index(base_line)
                        target_line_number = target_hunk_range_to_list[index_in_target_hunk]
                        single_line_map_base_to_target = LineMap(base_line_number, base_line, target_line_number, base_line)
                        self.single_line_maps.append(single_line_map_base_to_target)
                        self.interest_line_numbers_list.remove(line_num)
                        break
        if self.interest_line_numbers_list == []:
            all_no_change_mark = True
        return all_no_change_mark