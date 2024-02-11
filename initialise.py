"""
File for initialising all of the objects and classes used globally across this experiment.
Callables can therefore be imported from this file without needing to access the files that they are created in.
"""

import os
import tobii_research as tr
from numpy import asarray as arr
from numpy.random import choice as randchoice, seed

from psychopy import logging, visual, core, event, gui
import psychopy.iohub as io
from psychopy.hardware import keyboard
from psychopy.tools.filetools import fromFile

from helpers import Flash, Fade, Listen, LoopHandler, ExpHandler, Stim, Text, Partitions, ExpHandler, TrialData, LoopInfo, dict_unpack, rand_seed, write_file
from constants import p, e, w, t, l, s, trial_keys, name_dict

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
    """Generate a starting box to gather emails at the start of the experiment.

    Returns:
        gui.Dlg: The dialogue box for gathering emails
    """
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

def importDataOnRestart(filepath) -> ExpHandler:
    """Import data from a file to restart the experiment from the last position.

    Args:
        filepath (str): The path to the file to import

    Returns:
        ExpHandler: The handler object with data to restart from
    """
    if not os.path.isfile(filepath):
        raise Exception("Nonexistent file. Cannot import data to restart from last position!")
    
    # Initialise new handler by reading dictionary from file
    handler_dict: dict = fromFile(filepath)  # get information from handler file
    extra_info: dict = handler_dict.pop('extra_info')

    # Handle loops and trials by popping them and assigning them to dataclass using dict unpacking
    loops: list['LoopHandler'] = []
    for loop in handler_dict.pop('loops'):
        trials: list ['TrialData'] = [TrialData(**trial) for trial in loop.pop('trials')]
        loops.append(LoopHandler(**loop, trials=trials))
    exp_handler = ExpHandler(**handler_dict, loops=loops)  # automatically reassign all remaining values

    # Unpack settings from the extra_info in the file
    for key, value in extra_info.items():
        obj = globals()[name_dict[key]]
        obj = dict_unpack(obj, value)
    return exp_handler

def setupExpHandler() -> ExpHandler:
    """Make an ExperimentHandler object to handle trials and saving.

    Returns:
        ExpHandler: The handler object for this experiment with data to save
    """
    def setupTrialData(l: LoopInfo) -> list['TrialData']:
        """ Function to generate a list of TrialData objects for each trial in the loop. """
        # Initialise variables
        cond_probs, n_trials_per_block, n_blocks = arr(l.condition_probabilities), l.n_trials_per_block, l.n_blocks
        n_conds = len(cond_probs)
        cond_trial_nums = (n_trials_per_block*cond_probs).astype(int)

        # Check legal number of trials per condition
        if p.all_same_condition is False and sum(cond_trial_nums) != n_trials_per_block:
            raise ValueError("n_trials_per_block must divide into conditions!")
        
        loop_data = []
        for block in range(n_blocks):
            trial_start = block*n_trials_per_block
            block_trial_nums = cond_trial_nums.copy()  # 'remaining' numbers of each trial type

            for i in range(n_trials_per_block):
                # If we are using 'experimental' distribution of conditions
                if p.all_same_condition:
                    trial_cond = p.all_same_condition
                else:
                    trial_cond = randchoice(n_conds, p=block_trial_nums/sum(block_trial_nums))
                    block_trial_nums[trial_cond]-=1

                # Append TrialData object to loop_data
                loop_data.append(TrialData(
                    trial_n=trial_start+i,
                    trial_n_in_block=i,
                    block_n=block,
                    loop_n=l.loop_n,
                    trial_cond=trial_cond,
                    seed=rand_seed()))
        return loop_data

    loops = [LoopHandler(trials=setupTrialData(loop_info), loop_info=loop_info) for loop_info in l]
    return ExpHandler(data_filepath=e.filepath, save_pickle=p.save_pickle, loops=loops)

def setupLogging() -> logging.LogFile:
    """Set up a log file and determine the log level.
    LEVELS = DEBUG, INFO, EXP, DATA, WARNING, ERROR, CRITICAL (not used)

    Returns:
        logging.LogFile: The log file object
    """
    logging.console.setLevel(logging.ERROR)  # Control what gets output to console
    if p.save_log_file or p.check_framerate or p.record_framedrops:
        return logging.LogFile(e.filepath + '.log', level=logging.DATA)
    return None

def setupWindow() -> visual.Window:
    """Set up the experimental window to run the experiment in.

    Returns:
        visual.Window: The window object for the experiment
    """
    return visual.Window(
        size=w.screen_size, fullscr=p.fullscreen, screen=w.screen_n, checkTiming=False,
        winType='pyglet', allowStencil=False, color=[0,0,0], colorSpace='rgb', monitor='window1',
        backgroundImage='', backgroundFit='none',
        blendMode='avg', useFBO=True,
        units='height'
    )

def setupIo(win) -> io.launchHubServer:
    """Set up the io server.

    Args:
        win: The window object for the experiment

    Returns:
        io.launchHubServer: The io server object
    """
    # Setup iohub keyboard
    io_config = {}
    io_config['Keyboard'] = dict(use_keymap='psychopy')
    return io.launchHubServer(window=win, **io_config)

def setupEyetracker():
    """Set up the eyetracker.

    Returns:
        eyetracker: The eyetracker object or None if eyetracker is not used
    """
    if not p.use_eyetracker: return None
    all_trackers = tr.find_all_eyetrackers()
    if not all_trackers: raise Exception('no eyetracker found!')
    return(all_trackers[0])


# Objects for experiment - want to be accessed from multiple files.
seed(e.starting_seed)  # Set numpy seed
if p.use_eyetracker and p.save_eyetracker_data: write_file("", e.eye_data_filepath)  # create eyetracker save file
if p.show_gui: genStartingGui()

if p.restart_from_last: exp_handler = importDataOnRestart(f"{e.filepath}.psydat")
else: exp_handler = setupExpHandler()

win = setupWindow()
c = Components()
logfile = setupLogging()
io_server = setupIo(win=win)
eyetracker = setupEyetracker()
mouse = event.Mouse(win=win)
keypad = keyboard.Keyboard(backend='iohub')

# Custom classes
flash = Flash(t.flash_time, t.flashes_per_second, w.framerate)
fade = Fade(w.framerate, t.fade_time)
listen = Listen()