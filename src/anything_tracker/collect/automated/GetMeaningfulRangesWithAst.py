import ast
import random


class NodeRangeCollector(ast.NodeVisitor):
    def __init__(self):
        self.nodes_with_position = [] 

    def visit(self, node):
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno') \
                and hasattr(node, 'col_offset') and hasattr(node, 'end_col_offset'):
            self.nodes_with_position.append(node)
        else:
            pass

        self.generic_visit(node)

class GetMeaningfulRangesWithAst():
    def __init__(self, source_file, hint_ranges):
        self.source_file = source_file
        self.hint_ranges = hint_ranges 
        self.max_line_step = 20

        tmp = []
        for line_range in hint_ranges:
            tmp.extend(list(line_range))
        self.all_changed_lineno = sorted(set(tmp))
        
        # to return 
        self.selected_source_range = None 
        self.random_mark = None

    def run(self):
        with open(self.source_file, "r") as f: 
            code_for_parser = f.read()
        tree = ast.parse(code_for_parser)    
        # Collect all nodes with line ranges
        collector = NodeRangeCollector()
        collector.visit(tree)
        if not collector.nodes_with_position:
            return "No valid nodes found in the file."
        
        option = random.randint(0, 3)
        if option == 0: # 25%, randomly select several consective lines
            self.select_random_source_range()
            self.random_mark = "consective lines"
        else: 
            # 75%, because this option could also get entire line(s)
            # randomly select a valid node, even only select the nodes on changed lines, the node could also be non-change.
            self.change_operation = "involves in changed lines"
            nodes_involves_in_change = [node for node in collector.nodes_with_position 
                    if any(line in self.all_changed_lineno for line in list(range(node.lineno, node.end_lineno + 1)))]
            random_node = random.choice(nodes_involves_in_change)
            # all absolute linenos and col_offsets
            self.selected_source_range = [random_node.lineno, random_node.col_offset, 
                    random_node.end_lineno, random_node.end_col_offset]
            self.random_mark = "random node"

        return self.selected_source_range, self.random_mark
    
    def select_random_source_range(self):
        with open(self.source_file, "r") as f: 
            code_content = f.readlines()

        # start line
        start_lineno = None
        code_content_len = len(code_content)
        selected_range = random.choice(self.hint_ranges)
        range_size = len(list(selected_range))
        random_pre_line = random.randint(0, range_size) # x lines to add before the changed lines
        random_post_line = random.randint(0, range_size) # x lines to add after the changed lines
        range_end = min([(selected_range.stop + random_post_line), code_content_len])
        expend_for_selection = [selected_range.start - random_pre_line, range_end]
        start_lineno = random.choice(expend_for_selection)
        
        # end line
        end_lineno = None 
        max_end = start_lineno + self.max_line_step
        if max_end < code_content_len: 
            end_lineno = random.randint(start_lineno, max_end)
        
        # start and end col indices
        start_line = code_content[start_lineno - 1]
        start_idx = len(start_line) - len(start_line.lstrip()) + 1 # remove preceding whitespaces
        end_line = code_content[end_lineno - 1]
        end_idx = len(end_line.rstrip())
        # all absolute linenos and col_offsets
        self.selected_source_range = [start_lineno, start_idx, end_lineno, end_idx] 
 