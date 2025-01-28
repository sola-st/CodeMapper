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


def check_whether_keep_node(node, single_node=True):
    to_keep = True
    excluded_types = ['{', '}', '[', ']', '(', ')', '"', '\'', ':', ";", ".", ","]
    if single_node == False:
        # for consective nodes selection
        excluded_types = ['{', '}', '[', ']', '(', ')']
    if node.type in excluded_types:
        to_keep = False
    return to_keep

class NodeRangeCollector:
    def __init__(self):
        self.nodes_with_position = []

    def collect_positions(self, node, source_code):
        # Recursively traverse tree-sitter nodes and collect nodes with clear positions.
        if node.start_point and node.end_point:
            self.nodes_with_position.append(node)

        for child in node.children:
            self.collect_positions(child, source_code)

class GetMeaningfulRangesWithTreeSitter():
    def __init__(self, source_file, hint_ranges):
        self.source_file = source_file
        self.hint_ranges = hint_ranges 
        self.max_line_step = 20
        self.colloctor = None
        
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
        tmp = []
        for line_range in self.hint_ranges:
            tmp.extend(list(line_range))
        if 0 in tmp:
            tmp.remove(0)
            if not tmp:
                return None, None
        self.all_changed_lineno = sorted(set(tmp))
        option = random.randint(0, 2)
        # option = 2
        if option == 0: # 33.3%, randomly select several consective lines
            self.select_random_consective_lines()
        else: 
            # 66.7%, this option could also get entire line(s)
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
            
            self.nodes_involves_in_changed_lines = [node for node in self.collector.nodes_with_position 
                    if any(line in self.all_changed_lineno 
                            for line in list(range(node.start_point[0]+1, node.end_point[0] + 2)))]
            # randomly select a valid node inloved in changed lines, the node could also be non-change. 
            random_node = random.choice(self.nodes_involves_in_changed_lines)
            self.nodes_involves_in_changed_lines_backup = self.nodes_involves_in_changed_lines[:]
                
            if option == 1: # 33.3 %
                self.select_random_single_node(random_node)
            else: # 33.3 %
                self.select_random_consective_nodes(random_node)

        return self.selected_source_range, self.random_mark
    
    def select_random_single_node(self, random_node):
        while check_whether_keep_node(random_node) == False:
            # possible to get the same node
            self.nodes_involves_in_changed_lines_backup.remove(random_node)
            random_node = random.choice(self.nodes_involves_in_changed_lines_backup)
        # all absolute linenos and col_offsets
        start_lineno, start_column = random_node.start_point
        end_lineno, end_column = random_node.end_point 
        # random_node.end_point is an open end, the end bype is not included in "small" tree-sitter nodes
        # TODO To check: For larger nodes like function and class, it includes the end byte. 
        # So far, we skip them when do manual checking, since they are in another dataset.
        if end_column == 0:
            end_column = 1
        self.selected_source_range = [start_lineno + 1, start_column + 1, end_lineno + 1, end_column]
        self.random_mark = "random node"
        # print(f"**random node: {random_node.text.decode('utf-8')}")

    def select_random_consective_nodes(self, tmp_node):
        # tmp_node indicates an initial fuzzy location
        parent_node = tmp_node.parent  # a valid and meaningful bigger node.
        may_meaningful_child_nodes = []
        while not parent_node or len(may_meaningful_child_nodes) < 2:
            self.nodes_involves_in_changed_lines_backup.remove(tmp_node)
            tmp_node = random.choice(self.nodes_involves_in_changed_lines_backup)
            parent_node = tmp_node.parent
            may_meaningful_child_nodes = []
            for child in parent_node.children:
                if any(char.isalpha() or char.isdigit() for char in child.text.decode('utf-8')):
                    may_meaningful_child_nodes.append(child)

        backup = may_meaningful_child_nodes[:]
        random_start_node = random.choice(backup[:-1])
        # start_idx = parent_node.children.index(random_start_node)
        # if start_idx == 0:
        #     end_node = parent_node.children[-1]
        # else:
        idx = backup.index(random_start_node)
        end_node = random.choice(backup[idx+1:])
        
        start_lineno, start_column = random_start_node.start_point
        end_lineno, end_column = end_node.end_point 
        if end_column == 0:
            end_column = 1
        self.selected_source_range = [start_lineno + 1, start_column + 1, end_lineno + 1, end_column]
        self.random_mark = "random consective nodes"

        # end_idx = parent_node.children.index(end_node)
        # print(f"**random consective nodes: {''.join([node.text.decode('utf-8') for node in parent_node.children[start_idx: end_idx+1]])}")

    def select_random_consective_lines(self):
        with open(self.source_file, "r") as f: 
            code_content = f.readlines()

        code_content_len = len(code_content)
        selected_range = random.choice(self.hint_ranges)
        range_size = len(list(selected_range))
        random_pre_line = random.randint(0, range_size) # x lines to add before the changed lines
        expand_range_start = max([1, (selected_range.start - random_pre_line)])
        expand_range_for_start_selection = list(range(expand_range_start, selected_range.stop))
        if not expand_range_for_start_selection:
            return

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
        random_post_line = random.randint(0, range_size) # x lines to add after the changed lines
        expand_range_end = min([(selected_range.stop + random_post_line), code_content_len])
        expand_range_for_end_selection = list(range(start_lineno, expand_range_end))
        if expand_range_for_end_selection: 
            end_lineno = random.choice(expand_range_for_end_selection)
        else:
            end_lineno = start_lineno

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
        
