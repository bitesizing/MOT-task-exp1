""" File for Fade() class, which handles fade-ins and fade-outs of psychopy Text and Stim objects. 
Can handle individual and sequential fades, though sequential fades are currently very limited. 
"""

from collections import deque
from . import Text, Stim

class Fade():
    """ Small class to fade text and stimuli in and out. CURRENTLY ONLY ALLOWS ONE RATE OF FADING FOR QUEUE. could modify this to have individual stimuli fade in and out. """

    def __init__(self, framerate: float, fade_time: float=0.5):
        """
        framerate (float) : framerate of window; determines fading behaviour
        fade_time (float) : base time to fade in/out for, unless specific in functions
        """
        self.queue = deque()  # initialise as singly-linked lists
        self.sequential_queue = deque()  # initialise sequential_queue
        self.framerate = framerate
        self.increment = 1/(fade_time*self.framerate)  # amt. to increment fade by each frame
    
        # Useful values for handling fadeouts

    def append(self, item: object, fade_in: bool=True, reset: bool=True, increment=None, seq:bool=False):
        if increment is None: increment = self.increment
        if reset:
            if isinstance(item, Text): item.contrast = 0 if fade_in else 1
            else: item.opacity = 0 if fade_in else 1
        if seq: self.sequential_queue.append((item, increment * (1 if fade_in else -1)))
        else: self.queue.append((item, increment * (1 if fade_in else -1)))

    def extend(self, items: list[object], fade_in:bool=True, reset:bool=True, increment=None, seq:bool=False):
        if increment is None: increment = self.increment
        for item in items:
            self.append(item, fade_in=fade_in, reset=reset, increment=increment, seq=seq)
    
    def update(self):
        """ Updates the opacity of all stimuli in queue and out_queue by one frame.
        > Notably, there is a bug with TextStim() which means you cannot change their opacity after they have been set. Current workaround changes their contrast instead, but this means they will still block out things behind them. 
        """
        def updateTxt(txt_stim, increment):
            txt_stim.contrast += increment
            stopping_val = txt_stim.original_contrast if hasattr(txt_stim, 'original_contrast') else 1
            if txt_stim.contrast <= stopping_val: return False
            txt_stim.contrast = stopping_val
            return True
        
        def updateStim(stim, increment):
            stim.opacity += increment
            stopping_val = stim.original_opacity if hasattr(stim, 'original_opacity') else 1
            if stim.opacity < stopping_val: return False
            stim.opacity == stopping_val
            return True

        # Update normal queue
        idx = 0
        while len(self.queue) > idx:
            value, increment = self.queue[idx]
            updateItem = updateTxt if isinstance(value, Text) else updateStim
            if updateItem(value, increment):
                del self.queue[idx]
            else:
                idx += 1

        # Update sequential queue
        if self.sequential_queue:
            value, increment = self.sequential_queue[0]
            updateItem = updateTxt if isinstance(value, Text) else updateStim
            if updateItem(value, increment):
                self.sequential_queue.popleft()
