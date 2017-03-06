#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 13:48:14 2017

@author: patrick
"""

import matplotlib.pyplot as plt
import numpy as np

from .file import File

class SimplePlotter(object):
    def __init__(self, filename):
        self._file = File(filename)
        self.current = self._file.parameters["BunchCurrent"]
        
    def energy_spread(self):
        
        fig = plt.figure("Energy Spread - Current: "+str(self.current)+" A")
        fig.add_subplot(111)
        plt.plot(self._file.energy_spread[0], self._file.energy_spread[1])
        plt.xlabel("T in # Synchrotron Periods")
        plt.ylabel("Energy Spread") # TODO: Unit
        return fig
        
    def bunch_profile(self, period):
        if period not in self._file.bunch_profile[1]:
            print("Interpolating for usable period (using nearest)")
        idx = np.argmin(np.abs(np.array(self._file.bunch_profile[1])-period))
        fig = plt.figure("Bunch Profile - Current: "+str(self.current)+" A")
        fig.add_subplot(111)
        plt.plot(self._file.bunch_profile[0], self._file.bunch_profile[2][idx])
        # TODO: Labels
        return fig
    
    def bunch_length(self):
        fig = plt.figure("Bunch Length - Current: "+str(self.current)+" A")
        fig.add_subplot(111)
        plt.plot(self._file.bunch_length[0], self._file.bunch_length[1])
        plt.xlabel("T in # Synchrotron Periods")
        plt.ylabel("Bunch Length") # TODO: Unit
        return fig
    
    def csr_intensity(self):
        fig = plt.figure("CSR Intensity - Current: "+str(self.current)+" A")
        fig.add_subplot(111)
        plt.plot(self._file.csr_intensity[0], self._file.csr_intensity[1])
        plt.xlabel("T in # Synchrotron Periods")
        plt.ylabel("CSR Intensity") # TODO: Unit
        return fig
    
    def bunch_position(self):
        fig = plt.figure("Bunch Position - Current: "+str(self.current)+" A")
        fig.add_subplot(111)
        plt.plot(self._file.bunch_position[0], self._file.bunch_position[1])
        plt.xlabel("T in # Synchrotron Periods")
        plt.ylabel("Bunch Position") # TODO: Unit
        return fig    
    