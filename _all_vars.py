""" A file for initialising all the experimental variables, and most of the objects and classes used in this experiment.
Support files are grouped in two folders:
    1. (utils) : callables which do NOT rely on _all_vars. instances of these are typically made within this file. 
    2. (exp_help) : callables which DO rely on _all_vars. must be loaded into files after _all_vars. 
"""

import os
from pickle import TRUE
import numpy as np
from numpy import array as arr
import tobii_research as tr

from psychopy import data, logging, visual, core, event, gui
import psychopy.iohub as io
from psychopy.hardware import keyboard
from psychopy.tools.filetools import fromFile
from zmq import device

from utils import Flash, Fade, Listen, ExpHandler, Stim, Text, Partitions, device_presets

class TestingParameters():
    """ Experimental parameters for testing and debugging. """
    def __init__(self):
        # Saving options
        self.save_log_file = True
        self.save_csv = True
        self.save_pickle = True

        # Settings
        self.use_eyetracker = True          # use Tobii Fusion Pro eyetracker. False uses mouse
        self.show_gui = True                # show gui box to enter email, for lottery
        self.fullscreen = True              # run in fullscreen
        self.longer_initial_wait = True     # first stim. wait in a block will be at least 1s
        self.show_overlap = True            # shows stimulus overlap as feedback
        self.run_lottery = True             # runs the lottery, earning tickets

        # Modes and debugging
        self.check_framerate = False        # checks framrate of current monitor, prints to console
        self.record_framedrops = False      # logs frame drops to the console
        self.restart_from_last = False      # restarts from final position of selected .pickle file
        self.move_forever = False           # stimuli continue to move forever
        self.skip_response = False          # skip response portion of experiment
        self.all_same_condition = False     # if int sets all trials to trial_cond specified. False for usual proportions
p = TestingParameters()

class ExperimentalInfo():
    """ General info about the experiment and participant. """
    def __init__(self):
        # Manual vars
        self.pp_n = 1
        self.exp_name = 'MOT1'
        self.date = data.getDateStr()
        self.psychopy_version = '2023.2.3'
        self.device_name = os.environ['COMPUTERNAME']

        self.condition_probabilities = (0.6, 0.2, 0.2)
        self.n_trials_per_block = 45  #45
        self.n_blocks = 6  #6

        # Assign vars
        self.email = ""
        self.exp_start_time = self.exp_end_time = ""
        self.this_dir = os.path.dirname(os.path.abspath(__file__))
        self.overlap_per_block = []
        self.tickets_per_block = [0]*self.n_blocks
        self.filename = f'data/{self.exp_name}_'
        while os.path.isfile(f"{self.filename}pp{self.pp_n}.psydat"): self.pp_n += 1
        else:
            if p.restart_from_last: self.pp_n -= 1
        self.starting_seed = self.pp_n
e = ExperimentalInfo()

class DisplayInfo():
    """ Info about the experimental display. """
    def __init__(self):
        # Manual vars
        self.dimensions = arr([0.75, 0.75])
        self.centre = arr([0,0])
        self.partition_split = arr([2,2])
        self.spacing = arr([0.125, 0.125])
        self.fixation_radius = 0.1

        # Assign preset vars according to utils/device_presets.py
        self.screen_size = [1920, 1080]
        self.framerate = 60
        self.screen_n = 0
        if e.device_name in device_presets:
            for key, value in device_presets[e.device_name].items():
                setattr(self, key, value)

        # Additional vars
        self.screen_ratio = self.screen_size[0]/self.screen_size[1]
w = DisplayInfo()

class TimingInfo():
    """ Info about trial timing, in seconds. """
    def __init__(self):
        # Basic trial timing params
        self.wait_time = 0.5                # time stim wait for. 1s on first trial in block if set in 'p'
        self.flash_time = 0                 # time which stimuli 'flash' for
        self.trial_length = [3,7]           # min, max times of length of CONTROL trial

        # Experimental trial timing params
        self.max_cross_time = 6             # maximum time before a stimuli BEGINS attempting to cross
        self.max_change_time = 6.5          # minimum time before a stimuli BEGINS attempting to change
        self.post_cross_length = [0.2, 0.4] # min, max of time between cross and response
        self.post_change_length = [0.1, 0.3]# min, max of times between change and response

        # Other params
        self.max_response_time = 5          # max time for pp to respond before trial skipped
        self.break_time = 5                 # time at which you can proceed to next block during break
        self.fade_time = 0.5                # default time for text and stim to fade in when using fade class
        self.flashes_per_second = 1         # rate of flashing during flash phase
        self.max_nan_time = 1               # max time for eyetracker to report nan value
        self.max_gazebreak_time = 0.15      # max time for eyetracker to report broken gaze
t = TimingInfo()

class StimulusInfo(): 
    """ Info about trial stimuli"""
    def __init__(self): 
        # Input vars
        self.n = 4
        self.n_tracked = 4
        self.speed = 0.15
        self.r = 0.045

        # Additional vars
        self.speed_per_frame = self.speed / w.framerate
        self.d = self.r*2
s = StimulusInfo()


# Dictionary to show the structure of output data
trial_data = {
    'trial_n': None,
    'trial_n_in_block': None,
    'block_n': None,
    'trial_n_in_block': None,
    'seed': None,
    'trial_cond': None,

    # Timing
    'g_start_trial': None,
    'g_end_trial': None,

    't_start_moving': None,
    't_start_responding': None,
    't_get_response': None,

    'm_start_event_search': None,
    'm_event_occurs': None,

    'total_move_time': None,
    'total_search_time': None,
    'post_event_time': None,  #*
    'total_response_time': None,
    
    # Response identifiers
    'queried_id': None,
    'event_id': None,
    'response_pos': None,
    'queried_pos': None,
    'response_distance': None,
    'response_overlap': None,
    'n_tickets': 0,

    # Stim information
    'stim_info': {
        'bounces': [{
            'time': None,
            'vel': None,
            'pos': None
        }],
        'starting_vel': None,
        'starting_pos': None
    },
}
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

class Components():
    """ All stimuli objects used within the experiment. """
    def __init__(self) -> None:
        self.fixation = visual.ShapeStim(win, vertices='cross', size=(0.02,0.02), pos=(0,0),
            lineWidth=1.0, fillColor='black', lineColor=None)
        self.partitions = Partitions(w.dimensions, w.centre, w.spacing, w.partition_split, win=win)
        self.stims = [Stim(win, id=idx, size=(s.d, s.d), opacity=1, lineWidth=1.0, lineColor='white',
            fillColor='white') for idx in range(s.n)]
        self.feedback_stims = [Stim(win, id=idx, size=(s.d, s.d), opacity=0.5, lineWidth=1.0,
            lineColor=('white' if idx==0 else 'red'), fillColor=('white' if idx==0 else 'red')) for idx in range(2)]
        self.timeout_txt = Text(win, "Maximum response time reached.\n\n\nClick to continue.", color="white", height=0.05)
        self.great_response_txt = Text(win, "+1 ticket!", color="white", height=0.03)
        self.amazing_response_txt = Text(win, "+2 tickets!", color="white", height=0.03)
        self.distance_txt = [Text(win, f"{i}% overlap", pos=(0, 0), height=0.03) for i in range(101)]


""" ---------- FUNCTIONS IN ORDER OF RUNTIME ---------- """
def genStartingGui() -> gui.Dlg:
    """ Generate a starting box to gather emails at the start of the experiment. """
    # Generate different dialogue boxes depending on if set to restart from last position
    if p.restart_from_last:
        dlg = gui.Dlg(title='Restart from file...')
        dlg.addField('Participant number: ', e.pp_n, required=True, enabled=p.restart_from_last)
        ok_data = dlg.show()

        # Parse
        if dlg.OK == False: core.quit()
        e.pp_n = ok_data[0]
    else:
        dlg = gui.Dlg(title='Please enter your data!')
        dlg.addField('Participant number: ', e.pp_n, required=True, enabled=p.restart_from_last)
        dlg.addText('\nPlease leave the email field blank if you do NOT want to take part in the random lottery.', isFieldLabel=False)
        dlg.addField(label='Email: ', required=False)
        ok_data = dlg.show()

        # Parse
        if dlg.OK == False: core.quit()
        _, e.email = ok_data
        if e.email == "": p.run_lottery = False

def importDataOnRestart(e, w, t, s, trial_keys) -> ExpHandler:
    input_filename = f"{e.filename}pp{e.pp_n}.psydat"

    if not os.path.isfile(input_filename):
        raise Exception("Nonexistent file. Cannot import data to restart from last position!")
    
    # Get data from file
    exp_handler = fromFile(input_filename)  # get handler
    exp_handler.savePickle =p.save_pickle
    exp_handler.saveWideText = p.save_csv
    exp_handler.dataFileName += '_restart'

    # Reassign values
    info = exp_handler.extraInfo
    for key, value in info['experimental_info'].items(): setattr(e, key, value)
    for key, value in info['display_info'].items(): setattr(w, key, value)
    for key, value in info['timing_info'].items(): setattr(t, key, value)
    for key, value in info['stimulus_info'].items(): setattr(s, key, value)
    return exp_handler

def setupExpHandler(this_dir) -> ExpHandler:
    """ Make an ExperimentHandler object to handle trials and saving.
        dataDir (Path | str | None) : folder to save data to. set as None for current dir. 
        returns data.ExperimentHandler : handler object for this experiment with data to save
    """
    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    filename = f"{e.filename}pp{e.pp_n}"

    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        this_dir = os.path.commonprefix([this_dir, filename])
        filename = os.path.relpath(filename, this_dir)
    
    # an ExperimentHandler isn't essential but helps with data saving
    exp_handler = ExpHandler(
        name=e.exp_name, version='',
        originPath='C:\\Users\\hk23402\\Downloads\\myMOT2\\untitled.py',
        savePickle=p.save_pickle,
        saveWideText=p.save_csv,
        dataFileName=this_dir + os.sep + filename, sortColumns='time'
    )
    return exp_handler  # return experiment handler

def setupLogging(filename) -> logging.LogFile:
    """ Set up a log file and determine the log level.
    LEVELS = DEBUG, INFO, EXP, DATA, WARNING, ERROR, CRITICAL (not used)
        filename (str) : filename to save to, without extension  
    """
    logging.console.setLevel(logging.ERROR)  # Control what gets output to console
    if p.save_log_file or p.check_framerate:
        return logging.LogFile(filename+'.log', level=logging.DATA)
    else:
        return None

def setupWindow() -> visual.Window:
    """ Set up the experimental window to run the experiment in. """
    return visual.Window(
        size=w.screen_size, fullscr=p.fullscreen, screen=w.screen_n, checkTiming=False,
        winType='pyglet', allowStencil=False, color=[0,0,0], colorSpace='rgb', monitor='window1',
        backgroundImage='', backgroundFit='none',
        blendMode='avg', useFBO=True,
        units='height'
    )

def setupIo(win) -> io.launchHubServer:
    """ Set up io server """
    # Setup iohub keyboard
    io_config = {}
    io_config['Keyboard'] = dict(use_keymap='psychopy')
    return io.launchHubServer(window=win, **io_config)

def setupEyetracker(use_eyetracker: bool):
    if not use_eyetracker: return None
    all_trackers = tr.find_all_eyetrackers()
    if not all_trackers: raise Exception('no eyetracker found!')
    return(all_trackers[0])


# Objects for experiment - want to be accessed from multiple files.
if p.show_gui: genStartingGui()
if p.restart_from_last:
    exp_handler = importDataOnRestart(e, w, t, s, trial_keys)
else:
    exp_handler = setupExpHandler(e.this_dir)
win = setupWindow()
c = Components()
logfile = setupLogging(filename=exp_handler.dataFileName)
io_server = setupIo(win=win)
eyetracker = setupEyetracker(p.use_eyetracker)
mouse = event.Mouse(win=win)
keypad = keyboard.Keyboard(backend='iohub')

# Custom classes
flash = Flash(t.flash_time, t.flashes_per_second, w.framerate)
fade = Fade(w.framerate, t.fade_time)
listen = Listen()

