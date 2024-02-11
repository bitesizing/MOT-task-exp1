""" File for ExpHandler() subclass of Psychopy data.ExperimentHandler() class, primarily to remove uneeded values. """
import os
import pickle
from dataclasses import dataclass, field, fields, asdict, is_dataclass

from psychopy import data

from . import TrialData, write_file, LoopInfo

class MetaHandler(type):
    """ 
    Metaclass to dynamically create variables named after a string and add default variables to each class. 
    Defines custom metaclass methods for iteration, getting items by index, and the next method for iteration. 
    """

    def __new__(cls, name, bases, dct, items, this_item, n_items):
        # Dynamically create a variable named after a string
        setattr(cls, items, items)
        setattr(cls, this_item, this_item)
        setattr(cls, n_items, n_items)

        # Add variables by default to each class
        if items not in dct: dct[items] = []
        if this_item not in dct: dct[this_item] = -1
        @property
        def _n_items(self): return len(getattr(self, items))
        dct[n_items] = _n_items
        
        # Define custom metaclass methods
        # dct['__repr__'] = cls.custom_repr

        def custom_iter(self):
            """ Custom iterator. """
            # ALLOWS ITERATOR TO RESTART ON SAME VALUE IT QUIT ON.
            tmp_item = getattr(self, this_item)
            if tmp_item != -1:
                setattr(self, this_item, tmp_item-1)
            return self
        dct['__iter__'] = custom_iter  # add method to class

        def custom_next(self):
            """ Custom next method. """
            setattr(self, this_item, getattr(self, this_item) + 1)  # increment this_item
            if getattr(self, this_item) >= getattr(self, n_items): 
                setattr(self, this_item, -1)  # reset value
                raise StopIteration
            return getattr(self, items)[getattr(self, this_item)]
        dct['__next__'] = custom_next  # add method to class

        def custom_getitem(self, idx): return getattr(self, items)[idx]
        dct['__getitem__'] = custom_getitem
            
        # Create the class using the modified dictionary
        return super().__new__(cls, name, bases, dct)

# Example class using the custom metaclass    
@dataclass
class ExpHandler(metaclass=MetaHandler, items='loops', n_items='n_loops', this_item='this_loop'):
    """ Class to hold routines in the experiment. 

        Attributes:
            loops (list[LoopHandler]): List of LoopHandler objects.
            n_loops (int): Read-only property returning the number of loops.
            data_filepath (str): Path to the data file.
            save_pickle (bool): Whether to save the data as a pickle file.
            save_csv (bool): Whether to save the data as a CSV file.

        Methods:
            add_loop(self, loop_handler: 'LoopHandler'): Add a loop_handler to the exp_handler's loops.
            close(self): Close the exp_handler and save data if save_pickle is True.
            save_as_pickle(self, filepath): Save data as a pickle file.
    """
    data_filepath: str
    save_pickle: bool = True
    loops: list['LoopHandler'] = field(default_factory=list)
    this_loop: int = -1
    extra_info: dict = field(default_factory=dict)

    def add_loop(self, loop_handler: 'LoopHandler'):
        """ Add a loop_handler to the exp_handler's loops. """
        self.loops.append(loop_handler)
        loop_handler.exp_handler = self

    def close(self):
        if self.save_pickle: self.save_file()

    def save_file(self):
        """ General function to save a file """
        data = asdict(self)
        filepath = f'{self.data_filepath}.psydat'

        if os.path.exists(filepath):
            prefix, _, suffix = filepath.rpartition('.')
            mod = 1
            while os.path.exists(f'{prefix}_{mod}.{suffix}'): mod += 1
            filepath = f'{prefix}_{mod}.{suffix}'
        write_file(data, filepath)

@dataclass
class LoopHandler(metaclass=MetaHandler, items='trials', n_items='n_trials', this_item='this_trial'):
    """ Class to hold trials for each loop of the experiment.

        Attributes:
            trials (list): List of trials.
            n_trials (int): Read-only property returning the number of trials.
            exp_handler (ExpHandler): The exp_handler this loop belongs to.

        Methods:
            (None)
    """
    loop_info: LoopInfo = None
    trials: list['TrialData'] = field(default_factory=list)
    this_trial: int = -1
    # exp_handler: 'ExpHandler' = None