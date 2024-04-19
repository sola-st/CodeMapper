def convert_change_type(change_type, category):
    change_operation = None # to return
    change_operation_prefix = None

    # note: codetracker has no intra-file movements.
    # AnythingTracker: change, noChange, move, delete.
    # TODO check the deletions in codetracker.
    if category == "attribute":
        if change_type in ["introduced", "rename"]:
            change_operation_prefix = "change"
        else:
            change_operation_prefix = "noChange"
    # ... update for other categories.
    
    assert change_operation_prefix != None
    change_operation = f"{change_operation_prefix} ({change_type})"

    return change_operation
