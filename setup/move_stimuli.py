""" File for moveStimuli() function, which handles the movement of all stimuli within a frame.
This script calculates perfect elastic collisions, with realistic exchanges of speed between stimuli during collisions.
This is by far the messiest file in this script, would love to come back and neaten it sometime.
Ideally, stimulus movement would be handled by the stimuli themselves. This is tricky because of the way collisions between stimuli are handled, however.
"""

from numpy import abs, dot, arctan, array as arr
from numpy.linalg import norm as mag

from helpers import Stim, Partitions
from initialise import w

def moveStimuli(parent:Partitions, stim_list:list[Stim], collisions:bool=True, cross:bool=False, change:bool=False, trial_data:dict=None, time_on_flip:float=None):
    """ Moves all stimuli within a partition parent, including bounces, collisions, changes of direction and crosses. Modifies stim_list inplace. """

    def calcBounceTime(stim:Stim, partition:Partitions, isX:bool) -> float:
        """ Function to find the time in frames of a collision with an experimental boundary. 
            stim (Stim) : experimental stimulus. 
            partitions (Partitions) : object containing information about experimental boundaries.
            isX (float) : calculates boundaries with sides if True. Top and bottom if False.
            RETURNS float : time in fractions of a frame until next collision. float('inf') if more than a frame until collision.
            """
        if isX:
            pos, vel = stim.pos[0], stim.vel[0]
            min_, max_ = partition.min_x+stim.r, partition.max_x-stim.r
        else:
            pos, vel = stim.pos[1], stim.vel[1]
            min_, max_ = partition.min_y+stim.r, partition.max_y-stim.r

        if vel<0:
            dist = mag(pos-min_)
        elif vel>0:
            dist = mag(max_-pos)
        else: return float('inf')  # If velocity is exactly 0 in direction

        t = mag(dist/vel)  # needs to be positive
        return t

    def calcCollisionTime(stim_a, stim_b) -> float:
        """ Returns time in frames at which two stimuli collide. Refer to 'circle collisions' obsidian page for maths info. 
        -> t1 = start of frame
        -> t2 = time of collision (if exists)
        -> t3 = time where two stimuli would be closest
        -> t4 = end of frame 
            stim_a (Stim) : first stimulus object
            stim_b (Stim) : second stimulus object
            RETURNS float : time in frames at which the two stimuli collide. Less than one if used to calculate mid-frame positions. float('inf') if they never collide.
        """
        r_ba_t1 = stim_a.pos - stim_b.pos  # vector FROM b TO a at t1
        v_ab = stim_a.vel - stim_b.vel  # Relative velocity of a to b for all t (== v_ba)
        d_aa_t1t4 = mag(v_ab)  # Magnitude of total movement throughout the frame

        # 2) Find angle between r_pos and r_vel
        d_ab_t1 = mag(r_ba_t1)  # Distance between a and b at t1
        dot_vab_bat1 = dot(r_ba_t1, v_ab)
        if dot_vab_bat1 > 0: return float('inf')  # RETURN if stimuli are moving away from one another

        cos_theta = max(-1, min(1, dot_vab_bat1/(d_ab_t1*d_aa_t1t4)))  # Ensures -1 <= cos_theta <= 1
        sin_theta = (1-cos_theta**2)**0.5

        # 3) Calculate the closest distance between stimuli during the frame
        d_ab_t3 = sin_theta*d_ab_t1
        d_ab_t2 = (stim_a.r + stim_b.r)  # General equation faciliating different sized stimuli
        if d_ab_t3 >= d_ab_t2: return float('inf') # RETURN if no collision occurs

        # 4) Calculate the magnitude of relative velocity until the closest point
        d_aa_t1t3 = abs(cos_theta*d_ab_t1)  # This is the distance between stim a at t1 and t3

        # 5) Calculate the distance from the collision point to the 'closest' point using Pythagoras
        d_aa_t2t3 = (d_ab_t2**2 - d_ab_t3**2)**0.5
        d_aa_t1t2 = d_aa_t1t3 - d_aa_t2t3  # Calculate the distance to the collision point

        # 6) Calculate fraction of frame until t2 (point of collision)
        t = d_aa_t1t2 / d_aa_t1t4
        return t
    
    def calcVelocitiesAfterCollision(stim_a, stim_b):
        """ Function to calculate the new velocities of two stimuli after they collide.
            RETURNS tuple(new_v_a, new_v_b) : new stimulus velocities
        """
        # Take relative position and velocity of A and B
        r_ba_t2 = stim_a.pos - stim_b.pos  # Relative pos / direction vector from B to A
        v_ab = stim_a.vel - stim_b.vel

        # Take relative unit vector in the direction of the collision 
        u_ba_t2 = r_ba_t2 / mag(r_ba_t2)

        # Find velocity component in direction of B at time of collision
        s_ab_b_t2 = dot(v_ab, u_ba_t2)  # Speed of A relative to B in the direction B at t2
        Δv = s_ab_b_t2 * u_ba_t2  # Multiply speed by diretion to get velocity

        # Return new velocities of stim_a and stim_b
        return (stim_a.vel-Δv), (stim_b.vel+Δv)

    def moveStimulus(partition:Partitions, stim_i, idx, n, event_occurring=False):
        """ Main function to move each individual stimulus. 
        -> Iterates through each stimulus and calculates if any bounces or collisions are going to happen in the next frame. 
        -> If they are, calculates which one is going to happen first. 
        -> Moves both involved stimuli (just one if bounce) to point of collision and updates positions and velocities. 
        -> Recursively calculates collisions/bounces from new position until none. 
        -> Moves stimulus by velocity and resets values. 
        """
        collision_events = []
        t = stim_i.t  # percentage of frame with uncalculated movement

        # 1) Calculate if stimulus is going to bounce off a boundary in the next frame
        if stim_i.bounce:
            xbounce = calcBounceTime(stim_i, partition, isX=True)
            ybounce = calcBounceTime(stim_i, partition, isX=False)
            collision_events.extend([event for event in ((xbounce, "x"), (ybounce, "y")) if event[0]<t])

        # 2) Calculate if stim is going to collide with another stim in next frame
        if collisions == True:  # if stimuli are set to collide with each other
            for j in range(idx+1, n):
                stim_j = partition.stim_list[j]
                if not stim_i.bb.intersects(stim_j.bb): continue  # skip if no bounding box overlap
                collision_t = calcCollisionTime(stim_i, stim_j)
                if collision_t<t: collision_events.append((collision_t, stim_j.id))

        # 3) Move stimuli if no collisions
        if not collision_events:             
            # Calculate sudden change of directions
            if change and (stim_i.id == trial_data.event_id) and (stim_i.f_since_last_collision > w.framerate/4) and (min(xbounce, ybounce) > w.framerate/4):
                    stim_i.vel = arr([stim_i.vel[1], -stim_i.vel[0]])
                    event_occurring = True

            stim_i.pos += stim_i.vel*stim_i.t
            stim_i.f_since_last_collision += 1
            stim_i.update()  # Resets time value, calculates new bb
            return event_occurring # Return once stimuli have moved full distance for frame

        # 4) Otherwise process collisions and recall function
        t, collision_id = min(collision_events)
        stim_i.pos += stim_i.vel*t  # Update position of stim_i to point of collision

        if collision_id in ("x", "y"):
            is_x = True if collision_id=="x" else False

            # If stim set to cross the boundary
            if cross and trial_data.event_id is not None and stim_i.id==trial_data.event_id:
                bounce_angle = abs(arctan(stim_i.vel[0 if is_x else 1]/stim_i.vel[1 if is_x else 0]))

                # If angle >= 45 degrees
                if bounce_angle >= arctan(1):  # TODO set angle as variable
                    stim_i.bounce = False  # Turn off central bounces for that stim... change to phase? 
                    stim_i.pos += stim_i.vel*(1-t)
                    stim_i.update()  # Resets time value, calculates new bb
                    return True
            
            trial_data.stim_info[stim_i.id]['bounces'].append({
                'time': time_on_flip,
                'vel': stim_i.vel,
                'pos': stim_i.pos
            })
            stim_i.vel[0 if collision_id == "x" else 1] *= -1
            stim_i.f_since_last_collision = 0
            
        else:
            event_occurring = False  # If object collision happens before bounce, has_phased is still false
            stim_j = stim_list[collision_id]
            stim_j.pos += stim_j.vel*t  # Update pos. of stim_j to point of collision
            stim_i.vel, stim_j.vel = calcVelocitiesAfterCollision(stim_i, stim_j)
            stim_i.f_since_last_collision = stim_j.f_since_last_collision = 0
            
            # Update stim parameters post_collision, including new bounding box and new 't'  value
            stim_i.update(1-t)
            stim_j.update(1-t)
        return moveStimulus(partition, stim_i, idx, n, event_occurring)  # Recall function as 'i' has not yet moved full distance

    # Move each stimulus, one at a time. 
    event_occurring = False
    for partition in parent:  # can iterate through partitions using __iterable
        n = len(partition.stim_list)
        for idx in range(n):
            if moveStimulus(partition, partition.stim_list[idx], idx, n): event_occurring = True
    return event_occurring
    


