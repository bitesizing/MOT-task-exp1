""" File for calcStartData() function, which calculates the starting positions and parameters of all stimuli:
    - Assigns stimuli to partition
    - Randomly calculates non-overlapping starting positions of stimuli using grid-based system
    - Calculates random starting velocities of stimuli
    - Keeps track of tracked stimuli, queried stimuli, and event stimuli for each trial. 
"""
import numpy as np
from numpy import array as arr, sin, cos, pi
from numpy.random import uniform, choice as randchoice, shuffle

from helpers import Partitions, Stim, TrialData
from initialise import e, s, t, trial_keys

class Grid():
    def __init__(self, dimensions, n_cells, rad_arr):
        # Initialise starting grid
        self.dimensions: arr = dimensions
        self.cell_dimensions: arr = (dimensions*n_cells).astype(int)
        self.starting_grid: arr = np.zeros(self.cell_dimensions, dtype=bool)

        # Find lower left and upper right grid corners
        self.min_x, self.min_y = self.convertToGridCell(             rad_arr)
        self.max_x, self.max_y = self.convertToGridCell(dimensions - rad_arr)

        # Set inner grid values to True
        self.starting_grid[self.min_x+1:self.max_x, self.min_y+1:self.max_y] = True
    
    def reset_grid(self):
        """ Reset the grid to the starting state. """
        self.grid = np.copy(self.starting_grid)
    
    def update_grid(self, partition_min_pos):
        """ Function to update the grid with a bunch of values. """
        legal_cells = np.argwhere(self.grid==True)  # array of all legal positions
        cell_idx = legal_cells[randchoice(len(legal_cells))]  # choose random start cell
        self.setGridValues(cell_idx, self.min_x)  # add 'illegal' grid values inplace
        return self.convertToHeightUnits(cell_idx, partition_min_pos)
    
    def setGridValues(self, centre_cell, grid_rad_arr):
        """ Assigns a square 'block' of values in a 2d numpy array in the grid to 0. """
        min_x, min_y = np.maximum((0,0),            centre_cell - grid_rad_arr*2 - 1)
        max_x, max_y = np.minimum(self.grid.shape,  centre_cell + grid_rad_arr*2 + 1)
        self.grid[min_x:max_x, min_y:max_y] = 0

    def convertToGridCell(self, pos) -> arr:
        """ Converts 'height' unit information to 'grid cell' units. """
        result = pos * self.cell_dimensions
        return result.astype(int)

    def convertToHeightUnits(self, cell_coordinates, min_pos) -> arr:
        """ Converts 'grid cell' information to 'height' units. """
        result = (cell_coordinates / self.cell_dimensions) + min_pos
        cell_size_in_height = self.dimensions / self.cell_dimensions
        return uniform(result, result + cell_size_in_height)


def calc_start_data(partitions:Partitions, stims:list[Stim], n_tracked: int, trial_data:TrialData):
    """ Generates random starting velocities and (non-overlapping) starting positions for a list of stimuli and a given partition set.
        partitions (Partitions) : object containing information about window partitions.
        stims (list[Stim]) : list of stimuli to assign info to.
        trial_data (dict) : dict of data to record and pass to trialHandler
    """
    def random_velocity(speed) -> arr:
        """ Returns an [x, y] velocity vector with a random direction, scaled by speed """
        theta = uniform(high=2*pi)
        random_unit_vector = arr([sin(theta), cos(theta)])
        return random_unit_vector * speed

    def calc_tracker_per_partition(split, n_tracked) -> arr:
        """ Calculates the number of tracked stimuli per partition using alternating rows and columns where possible. No partition may have 2 more tracked stim than another.
            split (arr[1,2]) : n_columns and n_rows of partitions.
        """
        tracked = np.zeros(split)
        for _ in range(n_tracked):
            legal_idxs = []
            global_min = np.min(tracked)
            row_sum = np.sum(tracked, 0)
            row_idxs = np.where(row_sum == np.min(row_sum))[0]
            col_sum = np.sum(tracked, 1)
            col_idxs = np.where(col_sum == np.min(col_sum))[0]
            legal_idxs.extend((col_idx, row_idx) for col_idx in col_idxs for row_idx in row_idxs if tracked[col_idx, row_idx] == global_min)
            tracked[legal_idxs[randchoice(len(legal_idxs))]] += 1
        return tracked
    
    def calc_partition_data(cell_grid: Grid, partition: Partitions, start_idx: int, n_stim: int, n_tracked: int):
        """ Calculate all start data for a given partition. """
        cell_grid.reset_grid()  # reset grid to starting state

        partition.stim_list = []
        for i in range(n_stim):
            # Assign stim and reset values
            stim: Stim = stims[i+start_idx]
            stim.f_since_last_collision = float('inf')
            if not stim.bounce: stim.bounce = True

            # Calc partition ids
            stim.partition_id = partition.id
            partition.stim_list.append(stim)  # append stimuli to partition id 

            # Assign random velocity and random (non-overlapping) starting position
            stim.vel = random_velocity(s.speed_per_frame)
            stim.pos = cell_grid.update_grid(partition.min_pos)
            stim.is_tracked = True if i < n_tracked else False
            stim.update()  # create stim bounding box, etc. 

            # Pass information to trial data
            if (i < n_tracked): trial_data.tracked_ids.append(stim.id)
            trial_data.stim_info.append({'bounces': [], 'starting_vel': stim.vel, 'starting_pos': stim.pos})

    # Initialise variables
    n_stim = len(stims)
    cell_grid = Grid(dimensions=partitions.inner_dimensions, n_cells=1000, rad_arr=arr([stims[0].r, stims[0].r]))

    # Reset trial_data values that you asign to (in case of reset)
    trial_data.tracked_ids = []
    trial_data.stim_info = []

    # Assign tracked stimuli to partitions such that each col. or row must be filled before being given another tracked stim. 
    p_n_stim: int = int(n_stim/partitions.n)
    n_tracked_per_partition: arr = calc_tracker_per_partition(partitions.split, n_tracked)

    # Iterate through partitions and calculate starting params for each stimulus
    start_idx = 0
    for column_idx in range(partitions.columns):
        for row_idx in range(partitions.rows):
            partition_id = (column_idx, row_idx)
            calc_partition_data(cell_grid, partitions[partition_id], start_idx, p_n_stim, n_tracked_per_partition[partition_id])
            start_idx += p_n_stim  # Increment start_idx
    
    # Assign queried, tracked and move time to trial data
    shuffle_tracked = trial_data.tracked_ids.copy()
    shuffle(shuffle_tracked)
    trial_data.queried_id = shuffle_tracked.pop()  # assign queried id to trial data

    cond: str = trial_keys[trial_data.trial_cond]
    if cond in ("CROSSED", "CHANGED"):
        # Pop from shuffle_tracked if possible. 
        if shuffle_tracked:  trial_data.event_id = shuffle_tracked.pop()
        # Else take from other stimuli
        else: trial_data.event_id = randchoice([i for i in range(n_stim) if i != trial_data.queried_id])

        trial_length = t.trial_length
        if cond == "CROSSED":
            trial_length[1] = t.max_cross_time
            trial_data.move_times = [uniform(*trial_length), uniform(*t.post_cross_length)]
        elif cond == "CHANGED":
            trial_length[1] = t.max_change_time
            trial_data.move_times = [uniform(*trial_length), uniform(*t.post_change_length)]
    else:
        trial_data.move_times = [uniform(*t.trial_length)]