""" File for dataclass definitions, which are used to store variables defined in constants.py that are later used in the experiment. """
import os
import numpy as np
from numpy import asarray as arr
from dataclasses import dataclass, field, fields, MISSING

import psychopy
from psychopy import data

from . import device_presets

@dataclass
class TestingParameters():
    """ Class defining parameters related to testing and debugging.

    Attributes:
        restart_from_last (bool): restarts from final position of selected .pickle file
        use_eyetracker (bool): use Tobii Fusion Pro eyetracker. False uses mouse
        save_log_file (bool): save log file
        save_csv (bool): save csv file
        save_pickle (bool): save pickle file
        show_gui (bool): show gui box to enter email, for lottery
        fullscreen (bool): run in fullscreen
        longer_initial_wait (bool): first stim. wait in a block will be at least 1s
        show_overlap (bool): shows stimulus overlap as feedback
        run_lottery (bool): runs the lottery, earning tickets
        check_framerate (bool): checks framrate of current monitor, prints to console
        record_framedrops (bool): logs frame drops to the console
        move_forever (bool): stimuli continue to move forever
        skip_response (bool): skip response portion of experiment
        all_same_condition (bool): if int sets all trials to trial_cond specified. False for usual proportions
        skip_all_tracked_flash (bool): skip flash portion if all stimuli are being tracked
    """
    restart_from_last: bool
    use_eyetracker: bool 

    save_log_file: bool
    save_pickle: bool
    save_eyetracker_data: bool

    show_gui: bool
    fullscreen: bool             
    longer_initial_wait: bool         
    show_overlap: bool           
    run_lottery: bool

    check_framerate: bool     
    record_framedrops: bool
    move_forever: bool
    skip_response: bool
    all_same_condition: bool
    skip_all_tracked_flash: bool

@dataclass
class LoopInfo():
    """ Class defining parameters specific to each experimental routine.

    Attributes:
        condition_probabilities (list[float]): List of probabilities for each condition.
        n_trials_per_block (int): Number of trials per block.
        n_blocks (int): Number of blocks.
        n_tracked (int): Number of items tracked.
    """
    loop_n: int
    condition_probabilities: list[float]
    n_trials_per_block: int
    n_blocks: int
    n_tracked: int

    def __post_init__(self):
        self.n_trials_in_routine: int = self.n_blocks * self.n_trials_per_block
        self.overlap_per_block: list[float] = []
        self.tickets_per_block: list[int] = [0]*self.n_blocks

@dataclass
class ExperimentalInfo():
    """ Class defining general parameters about the participant and experiment.

    Attributes:
        exp_name (str): The name of the experiment.
        save_folder_name (str): The folder name for saving data.
        starting_pp_n (int): The starting participant number.
        psychopy_version (str): The version of Psychopy.
        email (str): The email of the participant.
        date (str): The date of the experiment.
        exp_start_time (str): The start time of the experiment.
        exp_end_time (str): The end time of the experiment.
        pp_n (int): The participant number.
    """
    exp_name: str
    save_folder_name: str
    starting_pp_n: int
    ROOT_DIR: str

    psychopy_version: str = psychopy.__version__
    email: str = ""
    date: str = data.getDateStr()
    exp_start_time: str = ""
    exp_end_time: str = ""

    # Assigned externally (with call to update())
    filepath: str = None
    eye_data_filepath: str = None
    pp_n: int = None
    starting_seed: int = None
    def update(self, restart_from_last: bool):
        """ Function to set the participant number to the highest number not present in the data folder."""
        pp_n = self.starting_pp_n
        while os.path.isfile(f'{self.save_folder_name}/{self.exp_name}_pp{pp_n}.psydat'):
            pp_n += 1
        if restart_from_last: pp_n -= 1

        # Set absolute filepath
        self.filepath = os.path.join(self.ROOT_DIR, f'{self.save_folder_name}/{self.exp_name}_pp{pp_n}')
        self.eye_data_filepath = self.filepath + "_eye_data.csv"
        self.pp_n = self.starting_seed = pp_n

@dataclass
class WindowInfo():
    """ Class defining parameters related to experiment window. 

    Attributes:
        dimensions (np.ndarray): The dimensions of the display.
        centre (np.ndarray): The coordinates of the center of the display.
        partition_split (np.ndarray): The partition split coordinates.
        spacing (np.ndarray): The spacing between elements on the display.
        fixation_radius (float): The radius of the fixation point.

        device_name (str): The name of the device.
        screen_size (list[int]): The size of the screen.
        framerate (int): The refresh rate of the screen.
        screen_n (int): The screen number.
    """
    dimensions: np.ndarray
    centre: np.ndarray
    partition_split: np.ndarray
    spacing: np.ndarray
    fixation_radius: float

    # Initialise default preset values
    device_name: str = os.environ['COMPUTERNAME']
    screen_size: list[int] = field(default_factory=lambda: [1920, 1080])
    framerate: int = 60
    screen_n: int = 0

    def __post_init__(self):
        # Assign presets from utils/device_presets.py (only works on init)
        if self.device_name in device_presets:
            for key, value in device_presets[self.device_name].items(): setattr(self, key, value)
        self.screen_ratio = self.screen_size[0]/self.screen_size[1]  # set ratio

@dataclass
class TimingInfo():
    """ Class defining parameters related to trial timing.

    Attributes:
        wait_time (float): Stimulus pre-movement wait time.
        flash_time (float): Stimulus flash time.
        trial_length (list): List containing the minimum and maximum length of control trials.
        max_cross_time (int): Maximum time before a stimuli begins attempting to cross.
        max_change_time (float): Minimum time before a stimuli begins attempting to change.
        post_cross_length (list): List containing the minimum and maximum time between cross and response.
        post_change_length (list): List containing the minimum and maximum times between change and response.
        max_response_time (int): Maximum time for participant to respond before trial is skipped.
        break_time (int): Time at which you can proceed to the next block during a break.
        fade_time (float): Default time for text and stimulus to fade in when using the fade class.
        flashes_per_second (int): Rate of flashing during flash phase.
        max_nan_time (int): Maximum time for eyetracker to report nan value.
        max_gazebreak_time (float): Maximum time for eyetracker to report broken gaze.
    """
    wait_time: float
    flash_time: float
    trial_length: list[int]
    max_cross_time: int
    max_change_time: float
    post_cross_length: list[float]
    post_change_length: list[float]
    max_response_time: int
    break_time: int
    fade_time: float
    flashes_per_second: int
    max_nan_time: int
    max_gazebreak_time: float

@dataclass
class StimulusInfo:
    """ Class defining parameters related to trial stimuli.

    Attributes:
        n (int): The number of stimuli.
        speed (float): The speed of the stimuli.
        r (float): The radius of the stimuli.
        d (float): The diameter of the stimuli, calculated as r * 2.
        speed_per_frame (float): The speed of the stimuli per frame, assigned externally.
    """
    n: int
    speed: float
    r: float

    def __post_init__(self):
        self.d: float = self.r * 2

    speed_per_frame: float = None  # assigned externally
    def update(self, framerate):
        self.speed_per_frame: float = self.speed / framerate

@dataclass(slots=True)
class TrialData:
    # If adding, check whether these fields get reset on 'reset-trial' or not
    trial_n: int
    trial_n_in_block: int
    block_n: int
    loop_n: int
    seed: int
    trial_cond: str

    is_complete: str = False

    # Timing
    move_times: arr = None
    g_start_trial: float = None
    g_end_trial: float = None
    t_start_moving: float = None
    t_start_responding: float = None
    t_get_response: float = None
    m_start_event_search: float = None
    m_event_occurs: float = None
    total_move_time: float = None
    total_search_time: float = None
    post_event_time: float = None
    total_response_time: float = None
    
    # Response identifiers
    tracked_ids: list[int] = field(default_factory = lambda: [])
    queried_id: int = None
    event_id: int = None
    response_pos: float = None
    response_vel: float = None
    queried_pos: float = None
    response_distance: float = None
    response_overlap: float = None
    n_tickets: int = 0

    stim_info: list = None
    """ Structure of stim_info:
    [{ 'bounces': [{
            'time': None,
            'vel': None,
            'pos': None
        }],
        'starting_vel': None,
        'starting_pos': None }] """

    def __setattr__(self, name, value):
        """ Override setattr class for custom message if illegal value is added. """
        if name not in self.__slots__:
            raise AttributeError(f"'{name}' must be added as an attribute in the TrialData class before you can assign to it!")
        object.__setattr__(self, name, value)

    def reset_optional(self, new_seed: int):
        """ Reset optional variables of the class. """
        for field in fields(self):
            if field.default is not MISSING:
                setattr(self, field.name, field.default)
            elif field.default_factory is not MISSING:
                setattr(self, field.name, field.default_factory())
        self.seed = new_seed
