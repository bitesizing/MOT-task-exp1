"""
File used to run the experiment.
Quite a simple file consisting mainly just of the run_all function containing the experimental loop. 
"""
import os
from numpy import array as arr
from dataclasses import asdict

from psychopy import prefs, plugins, core, data, logging
plugins.activatePlugins()
prefs.hardware['audioLib'] = 'ptb'
prefs.hardware['audioLatencyMode'] = '3'

from helpers import rand_seed, record_framedrops, TrialData
from initialise import e, p, w, t, l, exp_handler, logfile, io_server, win
from setup import ExpController, Trial


def check_framerate():
    """ Function to check the framerate of the experiment. """
    framerate = str(win.getActualFrameRate(nIdentical=1000, nMaxFrames=10000, nWarmUpFrames=100))
    logfile.write(framerate)

def run_all(exp_controller: ExpController):
    """ Run the experiment flow. Main function where things happen:) """
    # Clock and file variables
    os.chdir(_thisDir)  # make sure we're running in the directory for this experiment
    global_clock = core.Clock()  # to track the time since experiment started
    io_server.syncClock(global_clock)
    logging.setDefaultClock(global_clock)
    
    # Flip and start experiment
    win.flip()  # flip window to reset last flip timer
    e.exp_start_time = data.getDateStr(format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6)  #  store the exact time the global clock started
    if p.record_framedrops: record_framedrops(win, w.framerate)

    for loop_idx, loop_handler in enumerate(exp_handler):
        for trial_data in loop_handler:
            trial_data: TrialData
            trial_data.g_start_trial = global_clock.getTime()

            # Until trial is complete
            trial_response = 'continue'
            while trial_response != 'complete':
                trial = Trial(exp_handler=exp_handler, exp_controller=exp_controller)  # initialise trial class

                # For each iteration (reset) of a trial
                while trial_response == 'continue':
                    trial_response = trial.update_frame()
                
                # Handle resets
                if trial_response == 'reset':
                    trial_response = 'continue'  # reset trial response
                    exp_controller.show_gaze()  # show 'broken fixation' screen
                    trial_data.reset_optional(new_seed=rand_seed())  # reset optional values in data (which are set during trial)
            
            # Handle trial end
            trial_data.g_end_trial = global_clock.getTime()

            # Check if any values are still None
            for key, value in asdict(trial_data).items():
                if value is None:
                    print(f'{key} is None')

            # Handle breaks
            if (trial_data.trial_n+1) % (l[loop_idx].n_trials_per_block) == 0:
                exp_controller.show_break(trial_data)


""" ------------ RUN THE EXPERIMENT FROM START TO FINISH --------------"""
if __name__ == '__main__':  # If running the experiment as a script, not a module
    _thisDir = os.path.dirname(os.path.abspath(__file__))  # Ensure relative paths start from same dir. as this script

    # Call initialisation functions
    exp_controller = ExpController(break_time = t.break_time)
    if p.check_framerate: check_framerate()
    else: run_all(exp_controller)
    exp_controller.quit()
