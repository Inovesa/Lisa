# -*- coding: utf-8 -*-
"""
:Author: Patrick Schreiber
"""

from IPython.display import display, HTML
def display_video(mov):
    """Display Video certain video objects in Jupyter Notebooks"""
    display(HTML(mov.to_html5_video()))
