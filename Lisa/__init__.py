from .core import *

import os
__version__ = open(os.path.join(os.path.dirname(__file__),"VERSION"), "r").read().strip()

def is_sad():
    print("Lisa is sad.")
    return True