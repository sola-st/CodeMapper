import json
from os.path import join


def write_regions_to_files(results_dir, base_file_path, target_file_path,
                           source_character_range, target_character_range, 
                           source_region_characters_str, target_region_characters_str,
                           feedback=None):
    # TODO let users select the output folder in html.
    json_file = join(results_dir, "source_target_pair.json")
    if feedback != None:
        json_file = join(results_dir, f"source_target_pair_{feedback}.json")
    
    to_write:str = {
        "source_file": base_file_path,
        "target_file": target_file_path,
        "source_range": source_character_range,
        "target_range": target_character_range,
        "source_characters" : source_region_characters_str,
        "target_characters" : target_region_characters_str
    }
    # write tracked region pair to a JSON file.
    with open(json_file, "w") as ds:
        json.dump(to_write, ds, indent=4, ensure_ascii=False)