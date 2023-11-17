class Line():
    def __init__(self, number:int, source:str):
        self.number = number
        self.source = source

def show_line(__value: object):
    print(f"{__value.number}: {__value.source}")