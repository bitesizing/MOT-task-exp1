""" File for flatten() function, which returns all items in sub-lists and sub-dictionaries as 1-d struct for iteration purposes.
"""

def flatten(l):
    """ Iterates through d.values(), including through lists and sub-dictionaries. """
    if isinstance(l, dict): 
        for value in l.values():
            yield from flatten(value)
    elif isinstance(l, list):
        for value in l:
            yield from flatten(value)
    else:
        yield l