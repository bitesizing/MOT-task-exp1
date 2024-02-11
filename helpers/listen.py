""" File for Listen() class, designed to return True only if a mouse has gone from depressed to pressed. 
Helpful in avoiding bugs where e.g. holding the mouse down is counted as a click every frame. Ensures clicks are 'true' clicks. 
"""

from collections import defaultdict

class Listen():
    """ Listens for a True input following a False input. Useful in storing information about mouse buttons. """

    def __init__(self):
        self.has_been_false = defaultdict(lambda: False)

    def __repr__(self):
        return f"Listener for {list(self.has_been_false.keys())}"

    def listen(self, is_true:bool, id:str="") -> bool:
        """ Returns True if a True input occurs after a False input. 
        is_true (bool) : whether the input is currently True
        id (str) : identifier for specific input. defaults to "", but this can only be used once, unless self.reset is called
        """
        if self.has_been_false[id] and is_true: return True
        if not self.has_been_false[id] and not is_true: self.has_been_false[id] = True
        return False
    
    def reset(self, id:(str|list[str])="", reset_all=False):
        """ Resets a value for a given id. 
        id (str|list[str]) : identifies a specific input or set of inputs
        reset_all (bool) : resets all values in dict. defaults to False
        """
        if reset_all: self.has_been_false = defaultdict(lambda:False)
        elif isinstance(id, list):
            for string in id:
                self.reset(id=string)
        else: self.has_been_false[id] = False