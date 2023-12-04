""" File for ExpController() class, which handles screens and actions that occur within a trial:
    - Trial breaks between blocks
    - Gaze breaks away from central fixation
    - Pausing and quitting the experiment.
"""

from psychopy import core, logging, data
import tobii_research as tr

from utils import flatten, Text
from _all_vars import response_keys, exp_handler, win, eyetracker, mouse, keypad, listen, fade, p, e, w, t, s, trial_keys

class ExpController():
    """ Class to control experimental pausing and stopping. Differs from inbuilt ExperimentHandler because it does not store data, and has access to win. """

    def __init__(self):
        pass
    
    def listen_inputs(self, listen_continue:bool=False, timers:list[core.Clock()]=[], drawn_stim:list=[]) -> bool:
        """ Parent function to listen for 'pause' and 'quit' keys and perform appropriate function. Returns true to continue the current trial or section.
            listen_continue (bool) : listens for a 'continue' key to change to the next trial
        """
        if keypad.getKeys(keyList=[response_keys['pause_key']]): self.pause(timers=timers, drawn_stim=drawn_stim)
        if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()
        return True if listen_continue and keypad.getKeys(keyList=[response_keys['continue_key']]) else False

    def pause(self, timers:list[core.Clock()]=[], drawn_stim:list=[]):
        """ Pause this experiment, preventing the flow from advancing to the next routine until resumed.
            timers (list | tuple) : list of timers to reset once pausing is finished. defaults to empty tuple. 
            drawn_stim (dict) : dictionary of stimuli to keep drawing during the pause. defaults to empty. 
        """
        timer_pause_times = [timer.getTime() for timer in timers]  # Store pausetimes
        while True:
            # Check for pause or quit keys
            if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()
            if keypad.getKeys(keyList=[response_keys['pause_key']]): break

            # Draw current objects
            [stim.draw() for stim in flatten(drawn_stim)]
            win.flip()  # flip the screen
        
        # Reset timer values
        for timer, pause_time in zip(timers, timer_pause_times):
            # NOTE: This needs to be negative. This is a bug with the current version of Psychopy.
            timer.reset(-pause_time)  # resets the time in the timer to what it was at pause
            if timer.getTime() < 0: raise Exception('timer time is negative!')

    def showBreak(self, block_n:int, break_time:float=2):
        """ Display the 'break' screen inbetween blocks. 
            break_time (float) : time before you can click to end the break
            block_n (int) : which block has just ENDED
        """
        is_final_block = (block_n == e.n_blocks-1)
        mouse.setVisible(True)
        break_timer = core.Clock()

        txt = [
            Text(win=win, text="You have completed the block!", height=0.05, pos=(0,0.35)),
            Text(win=win, text=f"You responded with {int(e.overlap_per_block[block_n])}% average overlap", height=0.05, pos=(0,0.25)),
            Text(win=win, text=f"and earned {e.tickets_per_block[block_n]} ticket{'s' if e.tickets_per_block[block_n]!=1 else ''}.", height=0.05, pos=(0,0.18)),
            Text(win=win, text="Feel free to take a short break. The next block will begin shortly.", height=0.05, pos=(0,0.05))
        ]
        if is_final_block: del txt[3]
        if not p.run_lottery: del txt[2]
        fade.extend(txt, increment=1/(0.3*w.framerate), seq=True)  # append to spawn sequentially

        # Calc continue text (different if final block)
        continue_t = "You may now click to\nbegin the next block." if not is_final_block else "You have now completed the experiment :)\nYou may click to close this page."
        continue_txt = Text(win=win, text=continue_t, height=0.05, pos=(0,-0.2))

        listen.reset('continue_break')
        has_faded = False
        while True:
            if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()
            if is_final_block or win.getFutureFlipTime(clock=break_timer) >= break_time:
                if not has_faded:
                    has_faded = True
                    fade.append(continue_txt, seq=is_final_block)
                continue_txt.draw()
                if listen.listen(mouse.getPressed()[0], 'continue_break'):
                    break
            [t.draw() for t in txt]
            fade.update()
            win.flip()
    
    def showGaze(self):
        mouse.setVisible(True)
        listen.reset('continue_gaze')
        gaze_txt = Text(win=win, text=f"Please remain fixated on the central cross.\nClick to continue.", height=0.05, pos=(0,0.15))
        fade.append(gaze_txt)

        while not listen.listen(mouse.getPressed()[0], 'continue_gaze'):
            if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()
            gaze_txt.draw()
            fade.update()
            win.flip()
    
    def quit(self):
        """ Save data from the experiment, then end experiment, close window and quit. """
        win.flip()  # flip one last time so callOnFlip() tasks are executed
        if eyetracker is not None: eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA)
        logging.flush()

        # Adds extra_info to expHandler and saves data.
        e.exp_end_time = data.getDateStr(format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6)
        exp_handler.extraInfo = {
            "experimental_info": vars(e),
            "display_info": vars(w),
            "timing_info": vars(t),
            "stimulus_info": vars(s),
            "trial_keys": dict(trial_keys)}
        exp_handler.close()
        win.close()
        if p.record_framedrops:
            import matplotlib.pyplot as plt
            plt.plot(win.frameIntervals)
            plt.show()
        core.quit()