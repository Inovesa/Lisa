# -*- coding: utf-8 -*-
"""
Created on Mon Mar  28 14:44:32 2017

@author: patrick
"""

from IPython.display import display, HTML
def display_video(mov):
    display(HTML(mov.to_html5_video()))