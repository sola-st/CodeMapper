import random
import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_c_sharp as tscsharp
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_ruby as tsruby
import tree_sitter_typescript as tsts
import tree_sitter_php as tsphp
import tree_sitter_html as tshtml
from tree_sitter import Language, Parser


def check_whether_num_alpha_in_node_text(node):
    return any(char.isalpha() or char.isdigit() for char in node.text.decode('utf-8'))

def get_consective_unchanged_lines(line_list, start_num, max_line_num):
    start_idx = line_list.index(start_num)
    # at most with max_line_num unchanged lines
    to_iterate_list = line_list[start_idx: start_idx + max_line_num]
    end_num = start_num
    for num in to_iterate_list:
        if num == end_num + 1:
            end_num = num
        else:
            break
    return end_num

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
        self.colloctor = None
        
        # to return 
        self.selected_source_range = None 
        self.random_mark = None # node, consective sibling nodes, or consective lines
        self.change_ratio = ["non changed", "changed", "changed", "changed"] # 25% non-change VS. 75% change
        self.change_operation = random.choice(self.change_ratio)

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
        elif self.source_file.endswith(".ts"):
            CUR_LANGUAGE = Language(tsts.language_typescript())
        elif self.source_file.endswith(".php"):
            # Two options avaiable here: .language_php() and .language_php_only()
            # php_only is just php. The php parser parses php and html
            CUR_LANGUAGE = Language(tsphp.language_php())
        elif self.source_file.endswith(".html"):
            CUR_LANGUAGE = Language(tshtml.language())
        
        return Parser(CUR_LANGUAGE)

    def get_changed_unchanged_lines(self):
        tmp = []
        for line_range in self.hint_ranges:
            tmp.extend(list(line_range))
        if 0 in tmp:
            tmp.remove(0)
            if not tmp:
                return None, None, None, None
        self.all_changed_lineno = sorted(set(tmp)) # absolute numbers
        with open(self.source_file, "r") as f: 
            self.code_content = f.readlines()
        self.code_content_len = len(self.code_content)   
        self.all_non_changed_lineno = [line for line in range(1, self.code_content_len + 1) 
            if line not in self.all_changed_lineno] # absolute numbers
        # set the consective line size by referring to the average changed hunk size
        change_hunk_sizes = ([len(list(r)) for r in self.hint_ranges])
        self.avg_change_hunk_size = round(sum(change_hunk_sizes) / len(change_hunk_sizes))

    def run(self):
        self.get_changed_unchanged_lines()
        option = random.randint(0, 2)
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
                return "No valid nodes found in the file.", None, None, None

            # get nodes involvs in changed and non-changed lines, respectively
            nodes_involves_in_unchanged_lines = []
            nodes_involves_in_changed_lines = []
            for node in self.collector.nodes_with_position:
                if (node.end_point[0] - node.start_point[0]) < self.avg_change_hunk_size:
                    if any(line in self.all_changed_lineno for line in range(node.start_point[0] + 1, node.end_point[0] + 2)):
                        nodes_involves_in_changed_lines.append(node)
                    else:
                        nodes_involves_in_unchanged_lines.append(node)

            # randomly select a valid node
            # this could handle the change_operation selection for both the single node and consective sibling node cases
            self.to_select_list = []
            if self.change_operation == "non changed":
                if not nodes_involves_in_unchanged_lines:
                    return "No unchanged lines.", None, None, None 
                self.to_select_list = nodes_involves_in_unchanged_lines
            else:
                if not nodes_involves_in_changed_lines:
                    return "No expected changed lines.", None, None, None 
                self.to_select_list = nodes_involves_in_changed_lines
                self.test = nodes_involves_in_changed_lines[:]

            random_node = random.choice(self.to_select_list)
                
            if option == 1: # 33.3 %
                self.select_random_single_node(random_node)
            else: # 33.3 %
                self.select_random_consective_nodes(random_node)

        return self.selected_source_range, self.random_mark, self.change_operation, self.avg_change_hunk_size
    
    def select_random_single_node(self, random_node):
        end_lineno, end_column = random_node.end_point
        while check_whether_num_alpha_in_node_text(random_node) == False or end_column == False:
            # avoid to get the same node
            self.to_select_list.remove(random_node)
            if not self.to_select_list:
                return "No expected lines.", None, None, None 
            random_node = random.choice(self.to_select_list)
            end_lineno, end_column = random_node.end_point
        
        # all absolute linenos and col_offsets
        start_lineno, start_column = random_node.start_point
        # random_node.end_point is an open end, the end bype is not included in "small" tree-sitter nodes
        self.selected_source_range = [start_lineno + 1, start_column + 1, end_lineno + 1, end_column]
        self.random_mark = "random node"
        # print(f"**random node: {random_node.text.decode('utf-8')}")

    def get_desired_parent_node(self, node, parent_node):
        while not parent_node or len(parent_node.children) < 2 \
                or (parent_node.end_point[0] - parent_node.start_point[0]) > self.avg_change_hunk_size:
            self.to_select_list.remove(node)
            if not self.to_select_list:
                return None, None
            node = random.choice(self.to_select_list)
            parent_node = node.parent
        return node, parent_node

    def select_random_consective_nodes(self, tmp_node):
        # tmp_node indicates an initial fuzzy location
        parent_node = tmp_node.parent  # a valid and meaningful bigger node.
        tmp_node, parent_node = self.get_desired_parent_node(tmp_node, parent_node)
        if not parent_node:
            return

        backup = parent_node.children
        random_start_node = random.choice(backup[:1]) # avoid select a single node
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
        start_lineno = None
        start_line = None
        end_lineno = None
        if self.change_operation == "non changed":
            start_lineno = random.choice(self.all_non_changed_lineno)
            start_line = self.code_content[start_lineno - 1]
            while not start_line.strip():
                self.all_non_changed_lineno.remove(start_lineno)
                start_lineno = random.choice(self.all_non_changed_lineno)
                start_line = self.code_content[start_lineno - 1]
            end_lineno = get_consective_unchanged_lines(
                    self.all_non_changed_lineno, start_lineno, self.avg_change_hunk_size)
        else:
            start_lineno = random.choice(self.all_changed_lineno)
            start_line = self.code_content[start_lineno - 1]
            while not start_line.strip():
                self.all_changed_lineno.remove(start_lineno)
                if not self.all_changed_lineno:
                    return
                start_lineno = random.choice(self.all_changed_lineno)
                start_line = self.code_content[start_lineno - 1]
            end_lineno = min([start_lineno + self.avg_change_hunk_size - 1, self.code_content_len])

        end_line = self.code_content[end_lineno - 1]
        end_idx = len(end_line.rstrip())
        while end_idx == 0 and end_lineno > start_lineno:
            end_lineno -= 1
            end_line = self.code_content[end_lineno - 1]
            end_idx = len(end_line.rstrip())
        if end_idx == 0 :
            return
        
        # start and end col indices
        start_idx = len(start_line) - len(start_line.lstrip()) + 1 # remove preceding whitespaces
        # all absolute linenos and col_offsets
        self.selected_source_range = [start_lineno, start_idx, end_lineno, end_idx] 
        self.random_mark = "consective lines"
