class UnifyKeys():
    '''
    The data uses different keys for the 5 different categories, here unify the keys.
    '''
    
    def __init__(self):
        self.partial_categories = ["attribute", "variable"]
        self.group_1 = ["attribute", "variable", "block"]
        self.group_2 = ["method", "block"]
        self.key_set = {
            "attribute": {
                "start_name": "attributeName",
                "start_line_number": "attributeDeclarationLine"
            },
            "class": {
                "start_name": "className",
                "start_line_number": "classDeclarationLine",
                "start_info": "classKey"
            },
            "method" : {
                "start_name": "functionName",
                "start_line_number": "functionStartLine",
                "start_info": "methodKey"
            },
            "variable": {
                "start_name": "variableName",
                "start_line_number": "variableStartLine"
            },
            "block" : {
                "start_name": "blockName",
                "start_line_number": "blockStartLine",
                "end_line_number": "blockEndLine"
            }
        }