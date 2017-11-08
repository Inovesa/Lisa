from .internals import config_options, _check_compiled_version
from .plots import SimplePlotter, MultiPlot, setup_plots, PhaseSpace, MultiPhaseSpaceMovie, create_animation, data_frame_generator
if config_options.get("use_cython"):
    try:
        from .file_cython import File, MultiFile, Axis
        from ..core import file_cython as file
        _check_compiled_version(file)
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .file import File, MultiFile, Axis
        from ..core import file
    try:
        from .data_cython import Data
        from ..core import data_cython as data
        _check_compiled_version(data)
    except ImportError as e:
        print(e)
        print("Falling back to python implementation")
        from .data import Data
        from ..core import data
else:
    from .file import File, MultiFile, Axis
    from .data import Data
    from ..core import data, file



