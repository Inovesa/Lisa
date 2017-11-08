from ..internals import config_options, _check_compiled_version
from .animation import *
if config_options.get("use_cython"):
    try:
        from .plots_cython import *
        from ..plots import plots_cython as plots
        _check_compiled_version(plots)
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .plots import *
else:
    from .plots import *
