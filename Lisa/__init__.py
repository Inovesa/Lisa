from .plots import SimplePlotter, MultiPlot, setup_plots, PhaseSpace, MultiPhaseSpaceMovie, create_animation, data_frame_generator
from .data import File, MultiFile, Axis
from .data import Data

import os
__version__ = open(os.path.join(os.path.dirname(__file__), "VERSION"), 'r').readline().strip()
