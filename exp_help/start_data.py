""" File for calcStartData() function, which calculates the starting positions and parameters of all stimuli:
    - Assigns stimuli to partition
    - Randomly calculates non-overlapping starting positions of stimuli using grid-based system
    - Calculates random starting velocities of stimuli
    - Keeps track of tracked stimuli, queried stimuli, and event stimuli for each trial. 
"""

import numpy as np
from numpy import array as arr, sin, cos, pi
from numpy.random import uniform, choice as randchoice, shuffle

from utils import Partitions, Stim
from _all_vars import s, trial_keys

def calcStartData(partitions:Partitions, stims:list[Stim], trial_data:dict):
    """ Generates random starting velocities and (non-overlapping) starting positions for a list of stimuli and a given partition set.
        partitions (Partitions) : object containing information about window partitions.
        stims (list[Stim]) : list of stimuli to assign info to.
        trial_data (dict) : dict of data to record and pass to trialHandler
    """
    def randomVelocity(speed) -> arr:
        """ Returns an [x, y] velocity vector with a random direction, scaled by speed """
        theta = uniform(high=2*pi)
        random_unit_vector = arr([sin(theta), cos(theta)])
        return random_unit_vector * speed

    def setGridValues(grid, centre_cell, grid_rad_arr):
        """ Assigns a square 'block' of values in a 2d numpy array to 0. """
        min_x, min_y = np.maximum((0,0),      centre_cell - grid_rad_arr*2 - 1)
        max_x, max_y = np.minimum(grid.shape, centre_cell + grid_rad_arr*2 + 1)
        grid[min_x:max_x, min_y:max_y] = 0

    def convertToGridCell(pos, cell_dimensions) -> arr:
        """ Converts 'height' unit information to 'grid cell' units. """
        result = pos * cell_dimensions
        return result.astype(int)

    def convertToHeightUnits(cell_coordinates, cell_dimensions, dimensions, min_pos) -> arr:
        """ Converts 'grid cell' information to 'height' units. """
        result = (cell_coordinates / cell_dimensions) + min_pos
        cell_size_in_height = dimensions/cell_dimensions
        return uniform(result, result+cell_size_in_height)

    def calcTrackedPerPartition(split, n_tracked) -> arr:
        """ Calculates the number of tracked stimuli per partition using alternating rows and columns where possible. No partition may have 2 more tracked stim than another.
            split (arr[1,2]) : n_columns and n_rows of partitions.
        """
        tracked = np.zeros(split)
        for i in range(n_tracked):
            legal_idxs = []
            global_min = np.min(tracked)
            row_sum = np.sum(tracked, 0)
            row_idxs = np.where(row_sum == np.min(row_sum))[0]
            col_sum = np.sum(tracked, 1)
            col_idxs = np.where(col_sum == np.min(col_sum))[0]
            legal_idxs.extend((col_idx, row_idx) for col_idx in col_idxs for row_idx in row_idxs if tracked[col_idx, row_idx] == global_min)
            tracked[legal_idxs[randchoice(len(legal_idxs))]] += 1
        return tracked
    
    def calcPartition(start_pos_grid, partition, start_idx, n_stim, n_tracked):
        """ Calculate all start data for a given partition. """
        start_pos_grid = np.copy(start_pos_grid)  # Take copy of grid as this function is called multiple times.

        tracked_ids, partition.stim_list = [], []
        for i in range(n_stim):
            stim = stims[i+start_idx]
            info_dict = {'bounces':[]}
            stim_info.append(info_dict)

            # Reset values
            stim.t_since_last_collision = float('inf')
            if not stim.bounce: stim.bounce = True

            # Calc partition ids
            stim.partition_id = partition.id
            partition.stim_list.append(stim)  # append stimuli to partition id 

            # Assign velocity using set initial speed and random direction
            stim.vel = randomVelocity(initial_speed)
            info_dict['starting_vel'] = stim.vel
            
            # Handle tracking
            stim.is_tracked = True if i<n_tracked else False
            if (i<n_tracked): tracked_ids.append(stim.id)

            # Handle position by picking random starting position 
            legal_cells = np.argwhere(start_pos_grid==True)  # array of all legal positions
            cell_idx = legal_cells[randchoice(len(legal_cells))]  # choose random start cell
            stim.pos = convertToHeightUnits(cell_idx, cell_dimensions, dimensions, partition.min_pos)
            info_dict['starting_pos'] = stim.pos
            setGridValues(start_pos_grid, cell_idx, min_x)  # add 'illegal' grid values inplace

            # Update stim position values
            stim.update()  # create stim bounding box, etc. 
        return tracked_ids

    # Initialise variables
    if trial_data['seed'] is not None: np.random.seed(trial_data['seed'])  # Assign seed
    initial_speed, n_tracked, n_stim, rad_arr = s.speed_per_frame, s.n_tracked, len(stims), arr([stims[0].r, stims[0].r])
    dimensions, n_cells = partitions.inner_dimensions, 1000
    cell_dimensions = (dimensions*n_cells).astype(int)

    # Generate default spawn grid, with anything closer than radius to edge marked as illegal. 
    grid=np.zeros(cell_dimensions, dtype=bool)  # cell grid, default is False
    min_x, min_y = convertToGridCell(           rad_arr, cell_dimensions)  # Find ll and ur corners of grid
    max_x, max_y = convertToGridCell(dimensions-rad_arr, cell_dimensions)
    grid[min_x+1:max_x, min_y+1:max_y] = True  # Set inner values to True

    # Assign tracked stimuli to partitions such that each col. or row must be filled before being given another tracked stim. 
    p_n_stim = int(n_stim/partitions.n)
    p_n_tracked = calcTrackedPerPartition(partitions.split, n_tracked)

    # Iterate through partitions and calculate starting params. for each stimulus
    start_idx = 0
    stim_info = []
    trial_data["tracked_ids"] = []
    for column_idx in range(partitions.columns):
        for row_idx in range(partitions.rows):
            p_id = (column_idx, row_idx)
            trial_data["tracked_ids"].extend(calcPartition(grid, partitions[p_id], start_idx, p_n_stim, p_n_tracked[p_id]))
            start_idx += p_n_stim  # Increment start_idx
    
    # Add random 'queried' and 'tracked' to conds.
    shuffle_tracked = trial_data["tracked_ids"].copy()
    shuffle(shuffle_tracked)
    trial_data["queried_id"] = shuffle_tracked.pop()
    if trial_data["trial_cond"] in (trial_keys["CROSSED"], trial_keys["CHANGED"]):
        trial_data["event_id"] = shuffle_tracked.pop()
    return stim_info