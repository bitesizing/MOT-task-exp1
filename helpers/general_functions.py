from numpy.random import randint

def rand_seed() -> int:
    """ Function to calculate a random numpy seed."""
    return randint(0, 2**31-1)

def record_framedrops(win, framerate):
    win.recordFrameIntervals = True
    win.refreshThreshold = 1/framerate + 0.004

class Neut:
    """ Class which returns True to both True and False. """
    def __bool__(self):
        return True