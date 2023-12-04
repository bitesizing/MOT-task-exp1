""" Module for supporting callables which can be used for general purpose. These callables DON'T rely on _all_vars.  """

from .dict_utils import flatten
from .objects import Stim, Text, Partitions
from .handlers import ExpHandler

from .fade import Fade
from .flash import Flash
from .listen import Listen

from .device_presets import device_presets

__all__ = ['Fade', 'Flash', 'Listen', 'ExpHandler', 'flatten', 'Stim', 'Text', 'Partitions', 'moveStimuli', 'calcStartData', 'device_presets']