def compute_overlap(string1, string2):
    max_overlap = 0

    # Iterate over possible overlap lengths
    for i in range(1, min(len(string1), len(string2)) + 1):
        # Check if the end of string1 and the start of string2 have a common substring of length i
        if string1[-i:] == string2[:i]:
            max_overlap = i

    return max_overlap