#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Created on Mon Mar  6 13:48:14 2017

@author: patrick
"""

import matplotlib.pyplot as plt
import numpy as np

from .file import File

colors = [(0, 0, 1, 1), (0.8, 0.4, 0, 0.6), (1, 0, 1, 0.6), (0, 1, 1, 0.6), (1, 0, 0, 0.6),
          (0, 1, 0, 0.4)]
trans_value = 0.8

_simple_plotter_plot_methods = []

def setup_plots():  # todo arguments for latexify
    from blhelpers.plot_helpers import latexify
    latexify()

class SimplePlotter(object):
    """
    A Simple Plot Helper Class
    It takes a Filename to the Constructor.
    Each Method takes a optional label and a optional figure (kwarg fig)
    If fig is given the data is plotted into this figure
    """
    def __init__(self, filename):
        self._file = File(filename)
        self.current = self._file.parameters["BunchCurrent"]
        
    def plot(func):
        _simple_plotter_plot_methods.append(func.__name__)
        def decorated(*args, **kwargs):
            #if isinstance(args[-1], plt.Figure):
            #    fig = args[-1]
            #    ax = fig.add_subplot(111)
            scale_factor = kwargs["scale_factor"] if "scale_factor" in kwargs else 1.
            if ("fig" in kwargs and isinstance(kwargs["fig"], plt.Figure)):
                fig = kwargs["fig"]
                ax = fig.add_subplot(111)
            else:
                fig = plt.figure()
                ax = fig.add_subplot(111)
                kwargs["axes"] = ax
            x, y, xlabel, ylabel = func(*args, **kwargs) # arguments contain self object
            if(hasattr(fig, "num_of_plots")):   
                nop = fig.num_of_plots
                fig.num_of_plots += 1
            else:
                nop = 0
                fig.num_of_plots = 1
            if "label" in kwargs:
    #            ax.plot(x, y, label=kwargs["label"], color=colors[nop]) # do not use colors use default ones
                ax.plot(x, np.array(y)*scale_factor, label=kwargs["label"], alpha=(trans_value if nop > 0 else 1))
                ax.legend(loc="best")
            else:
    #            ax.plot(x, y, color=colors[nop]) # do not use colors use default ones
                ax.plot(x, np.array(y)*scale_factor, alpha=(trans_value if nop > 0 else 1))
            if(xlabel != "" and ax.get_xlabel()!="" and xlabel!=ax.get_xlabel()):
                xlabel = ax.get_xlabel()+"\n"+xlabel
            if(ylabel != "" and ax.get_ylabel()!="" and ylabel!=ax.get_ylabel()):
                ylabel = ax.get_ylabel()+"\n"+ylabel
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            return fig
        return decorated
        
    @plot
    def energy_spread(self, **kwargs):
        return(self._file.energy_spread[0], self._file.energy_spread[1], 
               "T in # Synchrotron Periods", "Energy Spread") # TODO: Unit
    
    @plot    
    def bunch_profile(self, period, **kwargs):
        if period not in self._file.bunch_profile[1]:
            print("Interpolating for usable period (using nearest): ",end="")
        idx = np.argmin(np.abs(np.array(self._file.bunch_profile[1])-period))
        print(self._file.bunch_profile[1][idx])
        return(self._file.bunch_profile[0], self._file.bunch_profile[2][idx],
               "", "") # TODO: Labels
               
    @plot
    def bunch_length(self, **kwargs):
        return (self._file.bunch_length[0], self._file.bunch_length[1],
                "T in # Synchrotron Periods", "Bunch Length") # TODO: Unit
                
    @plot
    def csr_intensity(self, **kwargs):
        return (self._file.csr_intensity[0], self._file.csr_intensity[1],
                "T in # Synchrotron Periods", "CSR Intensity") # TODO: Unit
                
    @plot
    def bunch_position(self, **kwargs):
        return (self._file.bunch_position[0], self._file.bunch_position[1],
                "T in # Synchrotron Periods", "Bunch Position") # TODO: Unit
                
class MultiPlot(object):
    def __init__(self):
        self._simple_plotters = []
        self._figure = plt.figure()
        
    def clone(self):
        mp = MultiPlot()
        mp._simple_plotters = self._simple_plotters
        return mp

    def add_file(self, filename, label=None):
        self._simple_plotters.append((SimplePlotter(filename), label))

    def reset(self):
        self._simple_plotters = []
        self._figure.clear()
        
    def possible_plots(self):
        return _simple_plotter_plot_methods

    def __getattr__(self, attr):
        if len(self._simple_plotters) == 0:
            def do_nothing():
                pass
            return  do_nothing # Return or do something like raise an exception?
        if hasattr(self._simple_plotters[0][0], attr):
            self._figure.clear()
            def inner(*args, **kwargs):
                kwargs["fig"] = self._figure
                for sp in self._simple_plotters:
                    if sp[1] != None:
                        kwargs["label"] = sp[1]
                    getattr(sp[0], attr)(*args, **kwargs)
                return self._figure
            return inner        
        else:
            raise Exception("MultiPlot does not have attribute " + attr)
    