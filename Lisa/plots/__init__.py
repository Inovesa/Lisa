from ..internals import config_options, _check_compiled_version
from .animation import create_animation, data_frame_generator
from .config import Style, Palette, palettes
if config_options.get("use_cython"):
    try:
        from .plots_cython import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
        from ..plots import plots_cython as plots
        _check_compiled_version(plots)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .plots import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
else:
    from .plots import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
