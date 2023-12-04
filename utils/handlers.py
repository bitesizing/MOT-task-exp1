""" File for ExpHandler() subclass of Psychopy data.ExperimentHandler() class, primarily to remove uneeded values. """

from psychopy import data

class ExpHandler(data.ExperimentHandler): 
    """ Override of the inbuilt psychopy experimentHandler class. """

    def nextEntry(self, add_extra:bool=False):
        """Calling nextEntry indicates to the ExperimentHandler that the
        current trial has ended and so further addData() calls correspond
        to the next trial.
        """
        this = self.thisEntry
        # fetch data from each (potentially-nested) loop
        for thisLoop in self.loopsUnfinished:
            names, vals = self._getLoopInfo(thisLoop)
            for n, name in enumerate(names):
                this[name] = vals[n]
        # add the extraInfo dict to the data
        if add_extra and type(self.extraInfo) == dict:
            this.update(self.extraInfo)
        self.entries.append(this)
        # add new entry with its
        self.thisEntry = {}
    
    def _getLoopInfo(self, loop, get_default:bool=False):
        """Returns the attribute names and values for the current trial
        of a particular loop. Does not return data inputs from the subject,
        only info relating to the trial execution.
        """
        names = []
        vals = []
        name = loop.name
        # standard attributes
        if get_default:
            for attr in ('thisRepN', 'thisTrialN', 'thisN', 'thisIndex',
                        'stepSizeCurrent'):
                if hasattr(loop, attr):
                    attrName = name + '.' + attr.replace('Current', '')
                    # append the attribute name and the current value
                    names.append(attrName)
                    vals.append(getattr(loop, attr))
        # method of constants
        if hasattr(loop, 'thisTrial'):
            trial = loop.thisTrial
            if hasattr(trial, 'items'):
                # is a TrialList object or a simple dict
                for attr, val in list(trial.items()):
                    if attr not in self._paramNamesSoFar:
                        self._paramNamesSoFar.append(attr)
                    names.append(attr)
                    vals.append(val)
        # single StairHandler
        elif hasattr(loop, 'intensities'):
            names.append(name + '.intensity')
            if len(loop.intensities) > 0:
                vals.append(loop.intensities[-1])
            else:
                vals.append(None)

        return names, vals