""" File for ExpController() class, which handles screens and actions that occur within a trial:
    - Trial breaks between blocks
    - Gaze breaks away from central fixation
    - Pausing and quitting the experiment.
"""
from dataclasses import asdict
import tobii_research as tr

from psychopy import core, logging, data

from helpers import flatten, Text, dict_pack, TrialData
from constants import response_keys, p, e, w, t, s, trial_keys, l, name_dict
from initialise import exp_handler, win, eyetracker, mouse, keypad, listen, fade

class ExpController():
    """ Class to control experimental pausing and stopping. Differs from inbuilt ExperimentHandler because it does not store data, and has access to win. """

    def __init__(self, break_time):
        self.break_time = break_time
    
    def listen_inputs(self, timers:list[core.Clock]=[], drawn_stim:list=[]) -> bool:
        """ Parent function to listen for 'pause' and 'quit' keys and perform appropriate function. Returns true to continue the current trial or section.
            listen_continue (bool) : listens for a 'continue' key to change to the next trial
        """
        if keypad.getKeys(keyList=[response_keys['pause_key']]): self.pause(timers=timers, drawn_stim=drawn_stim)
        if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()
        return True if keypad.getKeys(keyList=[response_keys['continue_key']]) else False

    def pause(self, timers:list[core.Clock]=[], drawn_stim:list=[]):
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
            if timer.getTime() < 0: raise Exception('timer time is negative! Bug must have been fixed... Revert back.')

    def show_break(self, trial_data: TrialData):
        """ Display the 'break' screen inbetween blocks. 
            break_time (float) : time before you can click to end the break
            block_n (int) : which block has just ENDED
        """
        mouse.setVisible(True)
        break_timer = core.Clock()
        block_n, loop_n, loop_info = trial_data.block_n, trial_data.loop_n, l[trial_data.loop_n]
        is_final_block, is_final_loop = (block_n == loop_info.n_blocks-1), (loop_n == len(l)-1), loop_info.tickets_per_block[block_n]
        n_tickets, p_overlap = loop_info.tickets_per_block[block_n], int(loop_info.overlap_per_block[block_n])

        text_options = [[
            {'text': "You have completed the block!",
             'pos': (0, 0.35)},
            {'text': f"You responded with {p_overlap}% average overlap",
             'pos': (0, 0.25)},
            {'text': f"and earned {n_tickets} ticket{'s' if n_tickets!=1 else ''}.",
             'pos': (0, 0.18),
             'include': p.run_lottery},
            {'text': "Feel free to take a short break. The next block will begin shortly.",
             'pos': (0, 0.05), 
             'include': not is_final_block},
        ], [
            # Continue text options
            {'text': f"You have now completed the experiment :)\nYou may click to close this page.", 
             'pos': (0, -0.2), 
             'include': is_final_block and is_final_loop},
            {'text': "You have finished the first experiment.\nPlease let the investigator know\nbefore continuing.", 
             'pos': (0, -0.2), 
             'include': is_final_block and not is_final_loop},
            {'text': f"You may now click to\nbegin the next block.",
             'pos': (0, -0.2), 
             'include': not is_final_block}     
        ]]
        text = [Text(**option) for option in text_options[0] if option.pop('include')]
        continue_text = [Text(**option) for option in text_options[1] if option.pop('include')]
        fade.extend(text, increment=1/(0.3*w.framerate), seq=True)  # append to spawn sequentially
        listen.reset('continue_break')

        # Main loop to draw text and listen for end break
        while True:
            if keypad.getKeys(keyList=[response_keys['quit_key']]): self.quit()

            if is_final_block or win.getFutureFlipTime(clock=break_timer) >= t.break_time:
                if continue_text not in text:
                    text.extend(continue_text)
                    fade.append(continue_text, seq=is_final_block)

                # Draw text and listen for end break
                if listen.listen(mouse.getPressed()[0], 'continue_break'): break

            [option.draw() for option in text]
            fade.update()
            win.flip()
    
    def show_gaze(self):
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

        # Add extra_info to handler and save data.
        e.exp_end_time = data.getDateStr(format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6)
        exp_handler.extra_info = {key: dict_pack(globals()[value]) for key, value in name_dict.items()}
        exp_handler.close()
        win.close()

        if p.record_framedrops:
            import matplotlib.pyplot as plt
            plt.plot(win.frameIntervals)
            plt.show()
        core.quit()