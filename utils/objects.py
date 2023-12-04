""" File for Stim() and Text() classes subclassed from similar Psychopy classes. Also handles custom Partition() class handling partitions of experimental window. """

from psychopy.visual.shape import ShapeStim
from psychopy.visual import TextStim
import numpy as np
from numpy import array as arr, minimum, maximum

class Stim(ShapeStim):
    """ Custom class inheriting from ShapeStim, to allow for additional variables. """
        
    def __init__(self, win, 
                vertices='circle',
                size:tuple=(1,1),
                pos=(0, 0),
                ori=0.0,
                fillColor=False,
                lineColor=False,
                lineWidth=1.0,
                opacity=1.0,

                # New
                id=0,
                vel=(0,0),
                partition_id=None,
                is_tracked=False,
                ):
        
        super().__init__(win=win, vertices=vertices, size=size, pos=pos, fillColor=fillColor, lineColor=lineColor, lineWidth=lineWidth, opacity=opacity, ori=ori, anchor='center')

        self.r = size[0]/2 if vertices=='circle' else None
        self.id = id
        self.t=1
        self.f_since_last_collision = float('inf')

        self.original_opacity = self.opacity

        self.base_colour = self.fillColor
        self.base_line_colour = self.lineColor
        self.partition_id = partition_id
        self.is_tracked = is_tracked
        self.bounce = True

        self.vel = vel
        self.bb = None  # Set on update

    # Update the position of a stimulus.
    def update(self, t=1):
        self.t = t
        self.bb = self.createBb(self.r, self.pos, self.vel*t)

    def updateSize(self, size):
        self.size = size
        self.r = size[0]/2
    
    def createBb(self, r:float, pos:arr, vel:arr) -> tuple:
        """ Calculates a bounding box for the movement of a stimulus during one frame, using its velocity.
        r (float) : radius of the stimulus
        pos (np.ndarray [(1,2)]) : current position of the stimulus
        vel (np.ndarray [(1,2)]) : velocity vector of the stimulus
        RETURNS tuple(centre, dimensions) : bb centre and WxH
        """

        # Calculate two opposite corners of the bounding box.
        vel = np.asarray(vel)
        corner = pos - np.sign(vel)*r
        opposite_corner = pos + vel + np.sign(vel)*r
        dimensions = abs(opposite_corner-corner)  # WxH
        centre = minimum(corner, opposite_corner) + dimensions*0.5
        return BoundingBox(dimensions, centre, win=self.win)


class BoundingBox(object):
    """ A custom bounding box object to store boundary information. Forms the basis of Partition. """

    def __init__(self, dimensions, centre, win=None, draw=False):
        self.dimensions = np.asarray(dimensions)
        self.centre = np.asarray(centre)
        self.width, self.height = self.dimensions
        self.win = win

        # Assign min- and max- coordinates
        self.min_x = self.centre[0] - self.width/2
        self.min_y = self.centre[1] - self.height/2
        self.max_x = self.centre[0] + self.width/2
        self.max_y = self.centre[1] + self.height/2
        self.min_pos = arr([self.min_x, self.min_y])
        self.max_pos = arr([self.max_x, self.max_y])

        # Generate stimulus - however, we only DRAW it for children. 
        if draw and self.win is not None:
            self.stim = Stim(
                win=win, vertices='rectangle',
                pos=self.centre, opacity=1, size=dimensions,
                lineWidth=1.0, lineColor='black', fillColor=None)

    def __repr__(self):
        return f"<BoundingBox: {self.min_x, self.min_y} to {self.max_x, self.max_y}"

    def intersects(self, other_bb) -> bool:
        """ Checks if another bounding box intersects with this bounding box.
            other_bb (BoundingBox) : the bounding box to check.
            RETURNS bool : `True` if they intersect, otherwise `False`.
        """
        return not (
            other_bb.min_x > self.max_x
            or other_bb.max_x < self.min_x
            or other_bb.max_y < self.min_y
            or other_bb.min_y > self.max_y
        )
    
    def contains(self, point):
            return (
            self.min_x <= point[0] <= self.max_x
            and self.min_y <= point[1] <= self.max_y
        )


class Partitions(BoundingBox):
    """ Stores the partitions of an experimental window. Returns parent partition, with references to children. Inherits basic features from BoundingBox. """

    def __init__(self, dimensions=(1,1), centre=(0,0), spacing=(0,0),
                 split=None, win=None, child=False, id=None):
        """
        dimensions (arr[2,1]) : array of width + height of outer partition (entire experimental window).
        centre (arr[2,1]) : array of outer partition centrepoint, in `height` units. 
        split (arr[2,1]) : array of columns and rows to divide window into, in that order.
        win (psychopy.visual.window) : window to draw partitions to. if None, doesn't draw
        child (bool) : True if this object is parent partition (full exp window). False if it is child.
        """

        super().__init__(dimensions, centre, win, draw=child)  # init bounding box
        self.index = 0  # allows iteration through __iter__ and __next__ functions
        self.id = id
        self.child = child
        self.stim_list = []
        
        # If parent, assign parent-specific values and generate children
        if not child:
            self.split = np.asarray(split)
            self.spacing = np.asarray(spacing)
            self.columns, self.rows = self.split
            self.n = np.prod(self.split)

            self.children = self.genPartitionChildren(outer_dimensions=self.dimensions, centre=self.centre, spacing=self.spacing, win=self.win, split=self.split)

            self.inner_dimensions = self.children[0, 0].dimensions
            self.inner_width, self.inner_height = self.inner_dimensions
    
    def __getitem__(self, idx):
        """ Returns what happens when accessed with square brackets. """
        idx = arr(idx)  # convert to np. array
        if self.child: raise TypeError("'Child' partition is not subscriptable")
        if not np.all((0<=idx) & (idx<self.children.shape)): raise IndexError("Index out of range")
        return self.children[tuple(idx)]  # convert back or code will treat it as slice
    
    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        """ Iterates through the children of a parent class. """
        if self.child: raise TypeError("'Child' partition cannot be iterated through.")
        if self.index < self.n:
            result = self[int(self.index/self.columns), self.index%self.rows]
            self.index += 1
            return result
        else:
            raise StopIteration

    def draw(self):
        if self.child: self.stim.draw()
        else: [child.stim.draw() for row in self.children for child in row]
    
    def setAutoDraw(self, auto_draw):
        if self.child: self.stim.setAutoDraw(auto_draw)
        else: [child.stim.setAutoDraw(auto_draw) for child in self.children]

    def genPartitionChildren(self, split, outer_dimensions, centre, spacing, win=None):
        """ Internal function to generate children for Partitions object. 
            RETURNS 2d array of child MyPartition objects with specified dimensions.
        """

        # Find the bottom left partition centre to begin from.
        inner_dimensions = (outer_dimensions - (split-1)*spacing) / split
        partition_centre = centre - 0.5*outer_dimensions + 0.5*inner_dimensions
        original_y = partition_centre[1]
        partitions=np.ndarray(tuple(split), dtype=Partitions)  # numpy array of Boundary objects. 

        # Iterate through to generate partitions
        for column in range(split[0]):
            partition_centre[1] = original_y
            for row in range(split[1]):
                partitions[column, row] = Partitions(
                    inner_dimensions, partition_centre,
                    win=win, child=True, id=(column, row))
                partition_centre[1] += inner_dimensions[1] + spacing[1]  # Increment centre of partition in y-axis
            partition_centre[0] += inner_dimensions[0] + spacing[0]  # Increment centre of partition in x-axis
        return partitions


class Text(TextStim):
    """ Text stim to do texty things. """

    def __init__(self, win, text,
                 height=0.03, pos=(0.0,0.0),
                 opacity=1, contrast=1,
                 align='center', color='white'):
        super().__init__(win=win, text=text, height=height, alignText=align, anchorHoriz=align, pos=pos, opacity=opacity, contrast=contrast, color=color)
        self.original_contrast = self.contrast
