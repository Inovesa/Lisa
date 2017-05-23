from .plots import SimplePlotter, MultiPlot, setup_plots, PhaseSpace, MultiPhaseSpaceMovie
try:
    from .file_cython import File
except ImportError as e:
    print(e)
    print("Falling back to python implementation")
    from .file import File
try:
    from .data_cython import Data
except ImportError as e:
    print(e)
    print("Falling back to python implementation")
    from .data import Data

#from .helpers import display_video
