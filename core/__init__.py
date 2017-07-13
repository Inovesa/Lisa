from .plots import SimplePlotter, MultiPlot, setup_plots, PhaseSpace, MultiPhaseSpaceMovie
from .internals import config_options
if config_options.get("use_cython"):
    try:
        from .file_cython import File, MultiFile
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .file import File, MultiFile
    try:
        from .data_cython import Data
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .data import Data
else:
    from .file import File, MultiFile
    from .data import Data

#from .helpers import display_video
