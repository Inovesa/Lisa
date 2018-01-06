from ..internals import config_options, _check_compiled_version
from .animation import create_animation, data_frame_generator
if config_options.get("use_cython"):
    try:
        from .config_cython import Style, Palette, palettes
        from ..plots import config_cython as configs
        _check_compiled_version(configs)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .plots import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
        from .config import Style, Palette, palettes
    try:
        from .plots_cython import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
        from ..plots import plots_cython as plots
        _check_compiled_version(plots)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .plots import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
else:
    from .config import Style, Palette, palettes
    from .plots import SimplePlotter, MultiPhaseSpaceMovie, MultiPlot, setup_plots, PhaseSpace
