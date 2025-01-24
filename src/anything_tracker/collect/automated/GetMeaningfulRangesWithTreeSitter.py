import random
import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_c_sharp as tscsharp
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_ruby as tsruby
# import tree_sitter_typescript as tsts
# import tree_sitter_php as tsphp
import tree_sitter_html as tshtml
from tree_sitter import Language, Parser


class NodeRangeCollector:
    def __init__(self):
        self.nodes_with_position = []

    def collect_positions(self, node, source_code):
        # Recursively traverse tree-sitter nodes and collect nodes with position info.
        if node.start_point and node.end_point:
            # TODO does the line and col always both exist
            self.nodes_with_position.append(node)

        for child in node.children:
            self.collect_positions(child, source_code)

class GetMeaningfulRangesWithTreeSitter():
    def __init__(self, source_file, hint_ranges):
        self.source_file = source_file
        self.hint_ranges = hint_ranges 
        self.max_line_step = 20
        self.max_node_step = 60

        self.colloctor = None

        tmp = []
        for line_range in hint_ranges:
            tmp.extend(list(line_range))
        self.all_changed_lineno = sorted(set(tmp))
        
        # to return 
        self.selected_source_range = None 
        self.random_mark = None

    def get_language_matched_parser(self):
        # add supported languages
        CUR_LANGUAGE = None
        if self.source_file.endswith(".py"):
            CUR_LANGUAGE = Language(tspython.language())
        elif self.source_file.endswith(".java"):
            CUR_LANGUAGE = Language(tsjava.language())
        elif self.source_file.endswith(".js"):
            CUR_LANGUAGE = Language(tsjs.language())
        elif self.source_file.endswith(".cs"):
            CUR_LANGUAGE = Language(tscsharp.language())
        elif self.source_file.endswith(".cpp"):
            CUR_LANGUAGE = Language(tscpp.language())
        elif self.source_file.endswith(".go"):
            CUR_LANGUAGE = Language(tsgo.language())
        elif self.source_file.endswith(".ruby"):
            CUR_LANGUAGE = Language(tsruby.language())
        # elif self.source_file.endswith(".ts"):
        #     # no binding repos for typescript and php, use another way to get language. 
        #     CUR_LANGUAGE = Language(tsts.language())
        # elif self.source_file.endswith(".php"):
        #     CUR_LANGUAGE = Language(tsphp.language())
        elif self.source_file.endswith(".html"):
            CUR_LANGUAGE = Language(tshtml.language())
        
        return Parser(CUR_LANGUAGE)

    def run(self):
        option = random.randint(0, 4)
        if option == 0: # 20%, randomly select several consective lines
            self.select_random_consective_lines()
        else: 
            # 80%, because this option could also get entire line(s)
            with open(self.source_file, "r") as f: 
                code_for_parser = f.read()

            parser = self.get_language_matched_parser()
            tree = parser.parse(bytes(code_for_parser, 'utf8'))
            root_node = tree.root_node
            self.collector = NodeRangeCollector()
            self.collector.collect_positions(root_node, code_for_parser)
            tree.walk()

            if not self.collector.nodes_with_position:
                return "No valid nodes found in the file.", None
            
            
            if option in [1, 2]: # 40 %
                self.select_random_single_node()
                self.random_mark = "random node"
            else: # 40 %
                self.select_random_consective_nodes()

        return self.selected_source_range, self.random_mark
    
    def select_random_single_node(self):
        # randomly select a valid node
        # even only select the nodes on changed lines, the node could also be non-change. 
        # TODO Avoid selecting meaningless nodes by checking their type, e.g., ')', ';', and '{'.
        # So far, just manual skip it.
        nodes_involves_in_changed_lines = [node for node in self.collector.nodes_with_position 
                if any(line in self.all_changed_lineno 
                        for line in list(range(node.start_point[0]+1, node.end_point[0] + 2)))]
        random_node = random.choice(nodes_involves_in_changed_lines)
        # all absolute linenos and col_offsets
        start_lineno, start_column = random_node.start_point
        end_lineno, end_column = random_node.end_point 
        # random_node.end_point is an open end, the end bype is not included in "small" tree-sitter nodes
        # TODO For larger nodes like function and class, it includes the end byte. 
        # So far, not using large nodes, since it is in another dataset.
        # if end_column == 0:
        #     end_column = 1
        self.selected_source_range = [start_lineno + 1, start_column + 1, end_lineno + 1, end_column]

    def select_random_consective_nodes(self):
        # Sort line_col ranges, + 1 to get abosulte numbers
        nodes_positions = sorted({(node.start_point[0] + 1, node.start_point[1] + 1, node.end_point[0] + 1, 
                node.end_point[1]) for node in self.collector.nodes_with_position})

        # Select a random node range and define a multi-line slice
        random_start = random.randint(0, len(nodes_positions) - 1)
        random_step = random.randint(2, self.max_node_step) # set 2 to avoid only a single node.
        # can set to 1 to cover the cases in select_random_single_node.
        selected_nodes_position = nodes_positions[random_start:random_start + random_step]
        if not selected_nodes_position:
            return "No sufficient nodes found for a multi-line range.", None

        # Extract the start and end positions
        start_lineno, start_idx, _, _ = selected_nodes_position[0]
        _, _, end_lineno, end_idx = selected_nodes_position[-1]
        self.selected_source_range = [start_lineno, start_idx, end_lineno, end_idx] 
        self.random_mark = "random consective nodes"

    def select_random_consective_lines(self):
        with open(self.source_file, "r") as f: 
            code_content = f.readlines()

        code_content_len = len(code_content)
        selected_range = random.choice(self.hint_ranges)
        range_size = len(list(selected_range))
        random_pre_line = random.randint(0, range_size) # x lines to add before the changed lines
        random_post_line = random.randint(0, range_size) # x lines to add after the changed lines
        expand_range_start = max([1, (selected_range.start - random_pre_line)])
        expand_range_end = min([(selected_range.stop + random_post_line), code_content_len])
        expand_range_for_start_selection = list(range(expand_range_start, expand_range_end))

        # start line
        start_lineno = random.choice(expand_range_for_start_selection)
        start_line = code_content[start_lineno - 1]
        while not start_line.strip():
            expand_range_for_start_selection.remove(start_lineno)
            if not expand_range_for_start_selection:
                return
            start_lineno = random.choice(expand_range_for_start_selection)
            start_line = code_content[start_lineno - 1]
        
        # end line
        end_lineno = None 
        max_end = start_lineno + self.max_line_step
        end = min([max_end, code_content_len])
        expand_range_for_end_selection = list(range(start_lineno, end))
        end_lineno = random.choice(expand_range_for_end_selection)

        end_line = code_content[end_lineno - 1]
        while not end_line.strip():
            expand_range_for_end_selection.remove(end_lineno)
            if not expand_range_for_end_selection:
                return
            end_lineno = random.choice(expand_range_for_end_selection)
            end_line = code_content[end_lineno - 1]

        # start and end col indices
        start_idx = len(start_line) - len(start_line.lstrip()) + 1 # remove preceding whitespaces
        end_idx = len(end_line.rstrip())
        # all absolute linenos and col_offsets
        self.selected_source_range = [start_lineno, start_idx, end_lineno, end_idx] 
        self.random_mark = "consective lines"
        
