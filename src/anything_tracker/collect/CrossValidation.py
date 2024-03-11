import json
from os.path import join


def read_annotations(file):
    with open(file, "r") as f:
        annotations = json.load(f)
    sorted_annotations = sorted(annotations, key=lambda x:x["mapping"]["source_commit"])
    return sorted_annotations


def cross_validation(annotation_file_1, annotation_file_2, differences_output):
    annotations_1 = read_annotations(annotation_file_1)
    annotations_2 = read_annotations(annotation_file_2)
    differences = []
    # idx = 0  
    for a1, a2 in zip(annotations_1, annotations_2):
        a1_mapping = a1["mapping"]
        a2_mapping = a2["mapping"]

        range_diff = False
        operation_diff = False

        if a1_mapping['target_range'] != a2_mapping['target_range']:
            range_diff = True

        if a1_mapping['change_operation'] != a2_mapping['change_operation']:
            operation_diff = True

        if range_diff == True or operation_diff == True:
            # sorted list make the idx a meaningless value, 
            # if want to keep the idx, keep 2 lists in the same order
            diff_dict = {
                    # "index(0)": idx,
                    "target_range_validate": "the same",
                    "change_operation_validate": "the same",
                    "notes":"" # allow to add details about the differences
                }
            if range_diff == True:
                diff_dict["target_range_validate"] = a2_mapping['target_range']
            if operation_diff == True:
                diff_dict["change_operation_validate"] = a2_mapping['change_operation']
            a1.update({"validation" : diff_dict})
            differences.append(a1)
        # idx+=1

    with open(differences_output, "w") as ds:
        json.dump(differences, ds, indent=4, ensure_ascii=False)


if __name__=="__main__":
    anno_folder = join("data", "annotation")
    annotation_file_1 = join(anno_folder, "annotations_a1.json")
    annotation_file_2 = join(anno_folder, "annotations_a2.json")
    differences_output = join(anno_folder, "differences.json")
    cross_validation(annotation_file_1, annotation_file_2, differences_output)