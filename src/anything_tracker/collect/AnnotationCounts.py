import json
from os.path import join


class AnnotationCounts():
    def __init__(self, annotaions_file):
        self.annotaions_file = annotaions_file
        self.change_operations = ["non changed", "changed", "moved", "deleted"]
        self.change_operations_count = [0, 0, 0, 0]
        self.kinds = ["neighboring", "distance"]
        self.kinds_count = [0, 0]
        self.categories = ["single identifier/word", "single expression/partial of sentence", 
                           "single line", "multiple line", "structural unit"]
        self.categories_count = [0, 0, 0, 0, 0]
        self.time_orders = ["old to new", "new to old"]
        self.time_orders_count = [0, 0]

    def count(self):
        with open(self.annotaions_file, "r") as f:
            annotations = json.load(f)
        for anno in annotations:
            mapping = anno["mapping"]

            # count change operations
            change_idx = self.change_operations.index(mapping["change_operation"])
            self.change_operations_count[change_idx] += 1

            # count kinds
            if mapping["kind"] == "neighboring":
                self.kinds_count[0] += 1
            else:
                self.kinds_count[1] += 1

            # count categories
            cate_idx = self.categories.index(mapping["category"])
            self.categories_count[cate_idx] += 1

            # count time_orders
            if mapping["time_order"] == "old to new":
                self.time_orders_count[0] += 1
            else:
                self.time_orders_count[1] += 1

        self.counted_results_to_dicts()

    def counted_results_to_dicts(self):
        change_operation_dict = dictformer(self.change_operations_count, self.change_operations)
        kind_dict = dictformer(self.kinds_count, self.kinds)
        category_dict = dictformer(self.categories_count, self.categories)
        time_dict = dictformer(self.time_orders_count, self.time_orders)
        
        to_write = {
            "change_operations": change_operation_dict,
            "kinds": kind_dict,
            "categories": category_dict,
            "time_orders": time_dict
        }
        with open(annotaions_file.replace(".json", "_counts.json"), "w") as f:
            json.dump(to_write, f, indent=4, ensure_ascii=False)
    

def dictformer(counts_list, value_list):
    result_dict = {}
    for i, value in zip(counts_list, value_list):
        result_dict.update({value: i})
    return result_dict


if __name__=="__main__":
    annotaions_file = join("data", "annotation", "annotations_100.json")
    AnnotationCounts(annotaions_file).count()

