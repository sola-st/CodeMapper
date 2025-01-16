import ast
import random


class NodeRangeCollector(ast.NodeVisitor):
    def visit(self, node):
        self.nodes_with_position = [] 
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno') \
                and hasattr(node, 'col_offset') and hasattr(node, 'end_col_offset'):
            self.nodes_with_position.append(node)
        self.generic_visit(node)

class GetMeaningfulRangesWithAst():
    def __init__(self, source_file, hint_ranges):
        self.source_file = source_file
        self.hint_ranges = hint_ranges 
        self.max_line_step = 20
        self.close_to_range_factor = 5 # a factor that close to change hunk line numbers
        self.change_rate = 0.9 # the source region involves in changes or not
        with open(source_file, "r") as f: 
            self.code_content = f.readlines()
        # to return 
        self.selected_source_range = None
        self.change_operation = None

    def run(self):
        tree = ast.parse(self.code_content)    
        # Collect all nodes with line ranges
        collector = NodeRangeCollector()
        collector.visit(tree)
        if not collector.nodes_with_position:
            return "No valid nodes found in the file."
        
        option = random.randint(0, 3) #TODO use random seed
        if option == 0: # 25%
            self.select_random_source_range()
        else: 
            # 75%, because this option could also get entire line(s)
            random_node = random.choice(collector.nodes_with_position) # Select a random node
            # TODO check whether it is consistant with existing source ranges
            # TODO use hint_ranges to guide the selection
            # TODO change_operation
            self.selected_source_range = [random_node.lineno, random_node.col_offset, 
                    random_node.end_lineno, random_node.end_col_offset]

        return self.selected_source_range, self.change_operation
    
    def select_random_source_range(self):
        # start line
        start_lineno = None
        code_content_len = len(self.code_content)
        selected_range = random.choice(self.hint_ranges)
        if random.random() < self.change_rate:
            start_lineno = random.randint(selected_range.start, selected_range.stop-1)
            self.change_operation = "changed"
        else: # get a line closer to changed lines
            close_linenobers = []
            pre_nums = list(range(selected_range.start - self.close_to_range_factor, selected_range.start))
            post_nums = list(range(selected_range.stop, selected_range.stop + self.close_to_range_factor))
            close_linenobers.extend(pre_nums)
            close_linenobers.extend(post_nums)
            start_lineno = random.choice(close_linenobers)
            self.change_operation = "non changed"
        
        # end line
        end_lineno = None 
        max_end = start_lineno + self.max_line_step
        if max_end + 1 < code_content_len: # 1 is used to avoid index out of range
            end_lineno = random.randint(start_lineno, max_end)
        
        # start and end col indices
        start_line = code_content_len[start_lineno - 1]
        start_idx = len(start_line) - len(start_line.lstrip()) # remove preceding whitespaces
        end_line = code_content_len[end_lineno - 1]
        end_idx = len(end_line) - len(end_line.rstrip())
        # TODO check whether it is consistant with existing source ranges
        self.selected_source_range = [start_lineno, start_idx, end_lineno, end_idx] 
 