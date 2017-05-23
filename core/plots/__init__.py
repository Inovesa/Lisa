try:
    from .plots_cython import *
except ImportError as e:
    print(e)
    print("Fallback to python version")
    from .plots import *
