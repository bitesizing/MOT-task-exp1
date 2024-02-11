""" File for Flash() class, which handles regular flashing of stimuli with highly customisable parameters.
Uses modified Gaussian distribution for nice flat-top flash. 
"""

import numpy as np
from numpy import array as arr
from scipy.stats import norm

class Flash():
    """ Small class to handle the flashing of stimuli to identify them as targets. """

    def __init__(self, total_time, flashes_ps, frames_ps, flash_colour=arr([1,-0.5,-0.5])):
        self.distribution, self.n_frames = self.calcFlashDistribution(total_time, flashes_ps, frames_ps)
        self.flash_colour = flash_colour
        
    def calcFlashDistribution(self, total_time, flashes_ps, frames_ps):
        """ Returns the distribution of colour that occurs when target stimuli 'flash' at the start of each trial. Uses a 'flatter top' Gaussian distribution. 
            total_time (float) : total time that stimuli need to be flashing for. This is the time before movement onset. 
            flashes_ps (float) : MINIMUM number of flashes per second. May need to be higher so flashes fit neatly into total_time. 
            frames_ps (float) : refresh_rate of the monitor you will be displaying the stimuli on.
            RETURNS distribution, frames_per_flash
        """
        # Initialise variables
        if total_time <=0: return [0], 1  # return 'empty' distribution if no flash time
        total_flashes = np.ceil(flashes_ps*total_time).astype(int)  # integer so we end on original colour, round up to have at least 1 flash. 
        flash_length = total_time/total_flashes  # Length of one flash in seconds
        frames_per_flash = int(frames_ps * flash_length)  # N. of frames per flash

        # Create Gaussian distribution
        x = np.linspace(-3, 3, frames_per_flash)  # One x-value per frame
        distribution = sum([norm.pdf(x, mean, 1) for mean in range(-1,2)])  # Sum three Gaussians with means -1, 0, 1
        distribution = (distribution-distribution[0]) / distribution[int(len(distribution)/2)]  # Set min- and max- values to 0 and 1 respectively.
        return distribution, frames_per_flash

    def flashStim(self, stim_list, frames_passed, flash_colour=None, flash_line=True):
        """ Changes colours of a list of target stimuli given a value (typically taken from a distribution)
            stim_list (Stim) : list of stimuli to modify
            frames_passed (int) : n_frames passed from start of flash. determines flash value
            flash_colour (np.array | None) : [R, G, B] colour with values in range [-1, 1]. defaults to class parameter.
            flash_line (bool) : if True, vary stim lineColor as well as fillColor. defaults to False.
        """
        if flash_colour is None: flash_colour = self.flash_colour
        value = self.distribution[frames_passed%self.n_frames]  # Set value using distribution

        for stim in stim_list:
            base_fill = stim.base_colour  # Take base colour from stimulus object
            base_line = stim.base_line_colour

            fill_difference = flash_colour-base_fill
            stim.fillColor = base_fill + fill_difference*value

            if flash_line:
                line_difference = flash_colour-base_line
                stim.lineColor = base_line + line_difference*value
        return frames_passed%self.n_frames

    def plot(self):
        """ Plot distribution. """
        from matplotlib.pyplot import plot as plt
        plt(self.distribution)  # Not sure if this will work without x-values? 
