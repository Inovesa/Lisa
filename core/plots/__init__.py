from ..internals import config_options
from .animation import *
if config_options.get("use_cython"):
    try:
        from .plots_cython import *
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .plots import *
else:
    from .plots import *
