""" THE FILE USED TO RUN THE EXPERIMENT.
Functions are listed in chronological order. The bottom portion of the file runs all functions in order to run the experiment.
Main supporting function used in this file is `exp_help/trial.py`, which handles everything about an individual trial.
"""

from psychopy import prefs, plugins, core, data, logging
plugins.activatePlugins()
prefs.hardware['audioLib'] = 'ptb'
prefs.hardware['audioLatencyMode'] = '3'

import os
import numpy as np
from numpy import array as arr
from numpy.random import randint, seed, choice as randchoice
from numpy.linalg import norm as mag

from _all_vars import e, p, w, t, trial_data as d, exp_handler, logfile, io_server, win
from exp_help import ExpController, Trial


def checkFramerate(exp_controller):
    framerate = str(win.getActualFrameRate(nIdentical=1000, nMaxFrames=10000, nWarmUpFrames=100))
    logfile.write(framerate)
    exp_controller.quit()

def randSeed() -> int:
    """ Function to calculate a random numpy seed. External function because it is called more than once."""
    return randint(0, 2**31-1)

def setupTrialData() -> list:
    cond_probs, n_conds, n_trials_per_block, n_blocks = arr(e.condition_probabilities), len(e.condition_probabilities), e.n_trials_per_block, e.n_blocks
    cond_trial_nums = (n_trials_per_block*cond_probs).astype(int)
    if p.all_same_condition is False and sum(cond_trial_nums) != n_trials_per_block: raise ValueError("n_trials_per_block must divide into conditions!")

    all_trial_data = []
    for block in range(n_blocks):
        block_trial_nums = cond_trial_nums.copy()  # 'remaining' numbers of each trial type

        for i in range(n_trials_per_block):
            trial_data: dict = d.copy()  # copy initial trial data

            # Add trial number and seed
            trial_data['trial_n'] = block*n_trials_per_block + i
            trial_data['trial_n_in_block'] = i
            trial_data['block_n'] = block
            trial_data['seed'] = randSeed()

            # If we are using 'experimental' distribution of conditions
            if p.all_same_condition is False:
                choice = randchoice(n_conds, p=block_trial_nums/sum(block_trial_nums))
                block_trial_nums[choice]-=1
                trial_data['trial_cond'] = choice
            
            # If all trials are the same condition
            else:
                trial_data['trial_cond'] = p.all_same_condition

            # Update values
            all_trial_data.append(trial_data)
    return all_trial_data


def runAll(exp_controller:ExpController):
    """ Run the experiment flow. Main function where things happen:) """
    # Initialise variables
    os.chdir(_thisDir)  # make sure we're running in the directory for this experiment
    global_clock = core.Clock()  # to track the time since experiment started
    io_server.syncClock(global_clock)
    logging.setDefaultClock(global_clock)
    
    # Generate trial conditions
    if p.restart_from_last:
        if exp_handler.loopsUnfinished == []: raise Exception('there are no unfinished loops!')
        trial_handler = exp_handler.loopsUnfinished[0]
        trial_data = trial_handler.thisTrial  # assign current (unfinished) trial
    else:
        trial_handler = data.TrialHandler(
            nReps=1, method='sequential', 
            extraInfo=None, originPath=-1,
            trialList=all_trial_data,
            seed=None, name='trials')
        exp_handler.addLoop(trial_handler)  # add the loop to the experiment
        trial_data = trial_handler.next()  # call first trial using .next()

    # Start recording framedrops if set to true
    if p.record_framedrops:
        win.recordFrameIntervals = True
        win.refreshThreshold = 1/w.framerate + 0.004
    
    # Flip and start experiment
    win.flip()  # flip window to reset last flip timer
    e.exp_start_time = data.getDateStr(format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6)  #  store the exact time the global clock started

    while True:
        # Run trial
        trial_data['g_start_trial'] = global_clock.getTime()
        trial = Trial(trial_data=trial_data, exp_controller=exp_controller)  # initialise trial class

        # Main loop that runs a full trial
        action = False
        while action is False:
            action = trial.updateFrame()

        # Handle trial resets by regenerating trial.
        if action == 'reset':
            exp_controller.showGaze()
            trial_data['seed'] = randSeed()
            continue
        trial_data['g_end_trial'] = global_clock.getTime()

        # Handle breaks
        if ((trial_data['trial_n']+1)%(e.n_trials_per_block))==0:
            exp_controller.showBreak(break_time=t.break_time, block_n=trial_data['block_n'])

        exp_handler.nextEntry()
        try: trial_data = trial_handler.next()
        except StopIteration: break  # trial_handler raises StopIteration on completion


""" ------------ RUN THE EXPERIMENT FROM START TO FINISH --------------"""
if __name__ == '__main__':  # If running the experiment as a script, not a module
    _thisDir = os.path.dirname(os.path.abspath(__file__))  # Ensure relative paths start from same dir. as this script
    seed(e.starting_seed)  # Set numpy seed

    # Call initialisation functions
    exp_controller = ExpController()
    if p.check_framerate: checkFramerate(exp_controller)
    all_trial_data = setupTrialData()
    
    # Run experiment 
    runAll(exp_controller)
    exp_controller.quit()
