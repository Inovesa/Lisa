from .internals import config_options
from .plots import SimplePlotter, MultiPlot, setup_plots, PhaseSpace, MultiPhaseSpaceMovie, create_animation, data_frame_generator
if config_options.get("use_cython"):
    try:
        from .file_cython import File, MultiFile, Axis, FileDataRegister
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .file import File, MultiFile, Axis, FileDataRegister
    try:
        from .data_cython import Data
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .data import Data
else:
    from .file import File, MultiFile, Axis, FileDataRegister
    from .data import Data

#from .helpers import display_video
