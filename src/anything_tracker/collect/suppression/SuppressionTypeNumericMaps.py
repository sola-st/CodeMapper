import csv
from os.path import join


class SuppressionTypeNumericMaps():
    def __init__(self, suppression_types, numerics):
        self.suppression_types = suppression_types # warning types
        self.numerics = numerics


def read_to_get_type_numeric_maps():
    suppression_types = []
    numerics = []

    suppression_oracle_folder = join("data", "oracle_suppression")
    numeric_type_map_file = join(suppression_oracle_folder, "specific_numeric_type_map.csv")
    with open(numeric_type_map_file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            suppression_types.append(row[0])
            numerics.append(row[1])

    maps = SuppressionTypeNumericMaps(suppression_types, numerics)
    return maps

def get_mapping_type(maps, numeric_code):
    # the idx always exists, because the nonexists is filtered out in the suppression study
    idx = maps.numerics.index(numeric_code) 
    mapping_type = maps.suppression_types[idx]
    return mapping_type

def get_mapping_numeric_code(maps, suppression_type):
    idx = maps.suppression_types.index(suppression_type) 
    mapping_numeric_code = maps.numerics[idx]
    return mapping_numeric_code