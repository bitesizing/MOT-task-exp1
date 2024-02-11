"""
File for initialising all the experimental variables, and most of the objects and classes used in this experiment.
Support files are grouped in two folders:
    1. (helpers) : callables which do NOT rely on constants.py. instances of these are typically made within this file. 
    2. (exp_help) : callables which DO rely on constants.py. must be loaded into files after constants is intialised. 
"""
import os
from numpy import asarray as arr

from helpers import TestingParameters, LoopInfo, ExperimentalInfo, WindowInfo, TimingInfo, StimulusInfo

p = TestingParameters(
    restart_from_last = False,
    use_eyetracker = True,

    save_log_file = False,
    save_pickle = False,
    save_eyetracker_data = True,

    show_gui = False,
    fullscreen = False,
    longer_initial_wait = True,
    show_overlap = True,
    
    run_lottery = True,
    check_framerate = False,
    record_framedrops = False,
    move_forever = False,
    skip_response = False,
    all_same_condition = False,
    skip_all_tracked_flash = True
)
l = [
    # Basic experiment
    LoopInfo(
        loop_n = 0,
        condition_probabilities = [0.6, 0.2, 0.2],
        n_trials_per_block = 45,
        n_blocks = 6,
        n_tracked=4,
    ),

    # Routine to test ceiling performance
    LoopInfo(
        loop_n = 1,
        condition_probabilities = [0.6, 0.2, 0.2],
        n_trials_per_block = 45,
        n_blocks = 2,
        n_tracked = 1,
    )
]
e = ExperimentalInfo(
    exp_name = 'MOT1',
    save_folder_name = 'data/final',
    starting_pp_n = 1,
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)),
)
e.update(restart_from_last = p.restart_from_last)
w = WindowInfo(
    dimensions = arr([0.75, 0.75]),
    centre = arr([0, 0]),
    partition_split = arr([2, 2]),
    spacing = arr([0.125, 0.125]),
    fixation_radius = 0.1,
)
t = TimingInfo(
    wait_time = 0.5, # 0.5,
    flash_time = 1,
    trial_length = [3,7],
    max_cross_time = 6,
    max_change_time = 6.5,
    post_cross_length = [0.2, 0.4],
    post_change_length = [0.1, 0.3],
    max_response_time = 5,
    break_time = 5,
    fade_time = 0.5,
    flashes_per_second = 1,
    max_nan_time = 2,
    max_gazebreak_time = 0.8,
)
s = StimulusInfo(
    n = 4,
    speed = 0.15,
    r = 0.045,
)
s.update(framerate = w.framerate)
trial_keys = {
    'CONTROL': 0,
    'CROSSED': 1,
    'CHANGED': 2, 
    0: 'CONTROL',
    1: 'CROSSED',
    2: 'CHANGED'
}
response_keys = {
    'quit_key': "escape",        # exits the experiment
    'pause_key': "numlock",      # pauses the experiment
    'continue_key': "semicolon"  # skips to next trial
}
name_dict = {'testing_parameters': 'p',
             'experimental_info': 'e',
             'loop_info': 'l',
             'window_info': 'w',
             'timing_info': 't',
             'stimulus_info': 's',
             'trial_keys': 'trial_keys'}