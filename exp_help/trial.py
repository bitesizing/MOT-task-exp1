""" File for Trial() class, handling everything about an individual trial. One instance is called per trial:
    - Updates movement of stimuli and events every frame
    - Handles eye-tracker fixation
    - Handles mouse clicks and location responses
    - Manages EventController() class to display screens
    - Runs through each trial subroutine iteratively
"""

from psychopy import core, logging, visual, event
from psychopy.visual import TextStim

import tobii_research as tr
import numpy as np
from numpy import array as arr
from numpy.random import seed, uniform
from numpy.linalg import norm as mag

from utils import flatten
from . import ExpController, calcStartData, moveStimuli

from _all_vars import p, e, w, t, s, c, trial_keys, win, mouse, flash, fade, listen, eyetracker

class Trial():
    """ Class handling an entire trial.
        trial_data (dict) : dict of trial parameters (e.g. cond, trial_length)
        exp_controller (ExpController) : controller object to handle pausing, quitting, breaks etc.
    """
    def __init__(self, trial_data:dict, exp_controller:ExpController):
        self.trial_data, self.exp_controller, self.condition = trial_data, exp_controller, trial_keys[trial_data['trial_cond']]
        seed(trial_data['seed'])  # assign numpy seed
        listen.reset(['response', 'timeout', 'feedback'])  # reset listener bc of old trials

        # Eyetracker vars
        if p.use_eyetracker:
            eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)  # begin subscribing
            self._eye_pos = None

        # Store stim move_time before and after 'event' (cross, change)
        if trial_data['trial_cond'] == trial_keys['CONTROL']:
            self.move_times = [uniform(*t.trial_length)]
        else:  # if exp. trial
            trial_length = t.trial_length
            if trial_data['trial_cond'] == trial_keys["CROSSED"]:
                trial_length[1] = t.max_cross_time
                self.move_times = [uniform(*trial_length), uniform(*t.post_cross_length)]
            elif trial_data['trial_cond'] == trial_keys['CHANGED']:
                trial_length[1] = t.max_change_time
                self.move_times = [uniform(*trial_length), uniform(*t.post_change_length)]

        # Calc starting data
        trial_data['stim_info'] = calcStartData(partitions=c.partitions, stims=c.stims, trial_data=self.trial_data)
        self.tracked_stims = [c.stims[id] for id in self.trial_data["tracked_ids"]]
        self.queried_stim = c.stims[self.trial_data["queried_id"]]
        if self.condition in ('CROSSED', 'CHANGED'): self.event_stim = c.stims[self.trial_data["event_id"]]
        
        # Routine and clock variables
        self.drawn_stim = []
        self.current_routine, self.first_access, self.tracked_n = self.startTrial, True, -1
        self.trial_timer, self.routine_timer, self.movement_timer, self.nan_timer, self.gazebreak_timer = core.Clock(), core.Clock(), core.Clock(), core.Clock(), core.Clock()
        win.callOnFlip(self.routine_timer.reset)  # resets routine clock on first flip... 

    def updateFrame(self) -> bool:
        """ Parent function to call the current subroutine using self.routines. Designed to be called every frame. 
            RETURNS bool : True if the experiment should be stopped
        """
        # Call current routine function from tuple. If -1, end trial
        new_routine = self.current_routine(self.first_access)
        if new_routine is None:
            self.first_access = False
        elif new_routine == -1:
            mouse.setPos((0,0))
            return True
        elif new_routine == -2:
            c.fixation.color='black'
            mouse.setVisible(True)
            return 'reset'
        else:
            self.current_routine, self.first_access = new_routine, True
            self.routine_timer = core.Clock()  # reset subroutine timer

        [stim.draw() for stim in flatten(self.drawn_stim)]
        logging.flush()
        win.flip()  # Flip the screen
        fade.update()
        return self.exp_controller.listen_inputs(listen_continue=True, timers=[self.routine_timer, self.trial_timer], drawn_stim=self.drawn_stim)

    @property
    def mouse_pos(self):
        """ Return the position of the mouse as a numpy array. """
        mouse_pos = arr(mouse.getPos())
        return mouse_pos
    
    @property    
    def inside_radius(self):
        if p.skip_response: return True
        fix_pos = self.eye_pos if p.use_eyetracker else self.mouse_pos
        if fix_pos is None: return False
        if mag(fix_pos)<=w.fixation_radius:
            self.gazebreak_timer.reset()
        elif self.gazebreak_timer.getTime()>t.max_gazebreak_time:
            return False
        return True
    
    @property
    def currently_inside_radius(self):
        fix_pos = self.eye_pos if p.use_eyetracker else self.mouse_pos
        if (fix_pos is None) or mag(fix_pos) > w.fixation_radius: return False
        return True
    
    @property
    def eye_pos(self):
        return self._eye_pos
    
    @eye_pos.setter
    def eye_pos(self, gaze_data):
        """ Convert raw data into usable height units."""
        height_pos = np.asarray(gaze_data)
        height_pos -= 0.5
        height_pos[0] *= w.screen_ratio
        self._eye_pos = height_pos

    def gaze_data_callback(self, gaze_data):
        """ Wrapper function used when querying eyetracker. Only updates if != nan. Tries both eyes. Prioritises left. """
        if self.nan_timer.getTime() > t.max_nan_time: self._eye_pos = None

        gaze_pos = gaze_data['left_gaze_point_on_display_area']  # try left eye
        if np.isnan(gaze_pos).any():  # try right eye if nan
            gaze_pos = gaze_data['right_gaze_point_on_display_area']
        if not np.isnan(gaze_pos).any():
            self.eye_pos = gaze_pos
            self.nan_timer.reset()

    def time_passed(self, timer: core.Clock()) -> float:
        """ Return time at next flip that will have passed for a given timer. """
        return win.getFutureFlipTime(clock=timer)
    

    # ~~~~~~~~~~ ROUTINE FUNCTIONS ~~~~~~~~~~
    def startTrial(self, first_access: bool=False):
        if first_access:
            if p.use_eyetracker: mouse.setVisible(False)
            self.drawn_stim = [c.partitions, c.fixation]

        if self.currently_inside_radius or p.skip_response:
            c.fixation.color = 'white'
            mouse.setVisible(False)
            return self.rInitialWait
    

    def rInitialWait(self, first_access: bool=False):
        if not self.inside_radius: return -2
        if first_access:
            self.drawn_stim = [c.stims, c.partitions, c.fixation]

        if p.longer_initial_wait and self.trial_data['trial_n_in_block'] == 0:
            if self.time_passed(self.routine_timer) >= max(1, t.wait_time):
                return self.rFlashStimuli
        else:
            if self.time_passed(self.routine_timer) >= t.wait_time:
                return self.rFlashStimuli
            

    def rFlashStimuli(self, first_access: bool=False):
        if not self.inside_radius: return -2
        if first_access: self.drawn_stim = [c.stims, c.partitions, c.fixation]
        flash.flashStim(self.tracked_stims, int(self.time_passed(self.routine_timer)*w.framerate))
        
        if self.time_passed(self.routine_timer) >= t.flash_time:
            flash.flashStim(self.tracked_stims, 0)  # reset flashing
            return self.rTrackStimuli


    def rTrackStimuli(self, first_access: bool=False):
        if not self.inside_radius: return -2
        if first_access:
            self.tracked_n += 1  # increment tracked number bc function gets called in different contexts
            if self.tracked_n == 0:
                self.trial_data['t_start_moving'] = win.getFutureFlipTime(clock=self.trial_timer)
                self.movement_timer.reset()
            self.drawn_stim = [c.stims, c.partitions, c.fixation]

        moveStimuli(c.partitions, c.stims, trial_data=self.trial_data, time_on_flip=self.time_passed(timer=self.trial_timer))
        if p.move_forever: return  # stim move forever, can be exited with exit_key
        if (self.time_passed(self.routine_timer) >= self.move_times[self.tracked_n]):
            if self.tracked_n == 1: self.trial_data['post_event_time'] = self.time_passed(self.movement_timer) - self.trial_data['m_event_occurs']
            if self.condition == 'CONTROL' or self.tracked_n == 1:
                return self.rGetResponse
            else:
                self.trial_data['m_start_event_search'] = self.time_passed(self.movement_timer)
                return self.rEvent
    

    def rEvent(self, first_access: bool=False):
        if not self.inside_radius: return -2
        if first_access:
            self.drawn_stim = [c.stims, c.partitions, c.fixation]
        
        # If stimulus starts to cross OR change direction
        if moveStimuli(c.partitions, c.stims,
                       cross=(True if self.condition == 'CROSSED' else False),
                       change=(True if self.condition == 'CHANGED' else False),
                       trial_data=self.trial_data, time_on_flip=self.time_passed(timer=self.trial_timer)):
            self.trial_data['m_event_occurs'] = self.time_passed(self.movement_timer)
            self.trial_data['total_search_time'] = self.trial_data['m_event_occurs'] - self.trial_data['m_start_event_search']
            return self.rTrackStimuli  # loop back to second phase of tracking
    

    def rGetResponse(self, first_access: bool=False):
        if p.skip_response: return -1
        if first_access:    
            mouse.setPos((0,0))
            c.fixation.color='black'
            self.trial_data['total_move_time'] = win.getFutureFlipTime(clock=self.movement_timer)
            self.trial_data['t_start_responding'] = self.time_passed(timer=self.trial_timer)
            c.partitions[self.queried_stim.partition_id].stim.lineColor = 'white'
            self.drawn_stim = [c.partitions, c.feedback_stims[0]]
            fade.append(c.feedback_stims[0])

        c.feedback_stims[0].pos = self.mouse_pos
        responded = listen.listen(mouse.getPressed()[0], id='response')

        # Time out if pp takes too long to respond
        if self.time_passed(self.routine_timer) >= t.max_response_time: return self.rTimeout

        # If response registered outside of correct partition, reset mouse listener.
        if responded and not c.partitions[tuple(self.queried_stim.partition_id)].contains(self.mouse_pos):
            listen.reset('response')
        
        # Trigger feedback if correct response registered
        elif responded:
            self.queried_pos, self.response_pos = self.queried_stim.pos, self.mouse_pos
            self.trial_data['queried_pos'], self.trial_data['response_pos'] = self.queried_pos, self.response_pos
            self.trial_data['t_get_response'] = self.time_passed(self.trial_timer)
            self.trial_data['total_response_time'] = self.time_passed(self.routine_timer)
            mouse.setVisible(False)
            return self.rGiveFeedback
    

    def rTimeout(self, first_access: bool=False):
        self.drawn_stim = [c.timeout_txt]
        if listen.listen(mouse.getPressed()[0], id='timeout'): return self.rEndTrial


    def rGiveFeedback(self, first_access: bool=False):
        if first_access:
            self.drawn_stim = [c.partitions, c.feedback_stims[1], c.feedback_stims[0]]
            c.feedback_stims[0].pos = self.response_pos
            c.feedback_stims[1].pos = self.queried_pos
            fade.append(c.feedback_stims[1])

            # Work out attributes of text
            txt_height = 0.03
            txt_buffer = txt_height * 1.2
            txt_on_right = 1 if self.queried_stim.partition_id[0] == 1 else -1
            x_pos = (c.partitions.inner_width + c.partitions.spacing[0])/2*txt_on_right
            bottom_y_pos = c.partitions[self.queried_stim.partition_id].max_y + txt_height/2 + (txt_buffer-txt_height)

            # Assign distance to trial_data
            response_distance = mag(self.response_pos-self.queried_pos)
            response_overlap = max((1-(response_distance/(s.r*2))), 0)  # can't be negative
            self.trial_data['response_distance'] = response_distance
            self.trial_data['response_overlap'] = response_overlap

            # Store percent overlap for block feedback
            percent_overlap = int(response_overlap*100)
            if self.trial_data['block_n'] >= len(e.overlap_per_block):
                e.overlap_per_block.append(percent_overlap/e.n_trials_per_block)
            else: e.overlap_per_block[self.trial_data['block_n']] += (percent_overlap/e.n_trials_per_block)

            # Generate text depending on how good the response was
            if response_distance <= s.d:
                if response_distance <= s.r:
                    feedback_txt = c.amazing_response_txt
                    self.trial_data['n_tickets'] += 2
                    e.tickets_per_block[self.trial_data['block_n']] += 2
                else:
                    feedback_txt = c.great_response_txt
                    self.trial_data['n_tickets'] += 1
                    e.tickets_per_block[self.trial_data['block_n']] += 1

                if p.run_lottery:
                    feedback_txt.pos = (x_pos, bottom_y_pos)
                    self.drawn_stim.append(feedback_txt)
                    fade.append(feedback_txt)
                distance_y_pos = bottom_y_pos+txt_buffer
            else:
                distance_y_pos = bottom_y_pos

            # Show distance if parameter set to True
            if p.show_overlap:
                current_txt = c.distance_txt[percent_overlap]
                current_txt.pos = (x_pos, distance_y_pos)
                fade.append(current_txt)
                self.drawn_stim.append(current_txt)
        if listen.listen(mouse.getPressed()[0], id='feedback'): return self.rEndTrial
    

    def rEndTrial(self, first_access:bool=False):
        c.partitions[self.queried_stim.partition_id].stim.lineColor = 'black'
        return -1  # end trial
