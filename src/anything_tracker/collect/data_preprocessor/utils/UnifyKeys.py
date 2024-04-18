class UnifyKeys():
    '''
    The data uses different keys for the 5 different categories, here unify the keys.
    '''
    
    def __init__(self):
        self.partial_categoris = ["attribute", "variable"]
        self.key_set = {
            "attribute": {
                "to_split": "attributeKey",
                "start_line_number": "attributeDeclarationLine"
            },
            "class": {
                # "to_split": "classKey",
                "start_line_number": "classDeclarationLine"
            },
            # "method" : {
            #     "to_split": "functionKey",
            #     "start_line_number": "functionStartLine"
            # },
            "variable": {
                "to_split": "variableKey",
                "start_line_number": "variableStartLine"
            },
            "block" : {
                "to_split": "blockKey",
                "start_line_number": "blockStartLine",
                "end_line_number": "blockEndLine"
            }
        }