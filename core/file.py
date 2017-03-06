#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 13:19:04 2017

@author: patrick
"""

import h5py as h5

class File(object):
    def __init__(self, filename):
        self.filename = filename
        self.file = h5.File(filename, 'r')
        self._bunch_length = None
        self._bunch_position = None
        self._bunch_population = None
        self._bunch_profile = None
        self._csr_intensity = None
        self._csr_spectrum = None
        self._energy_profile = None
        self._energy_spread = None
        self._impedance = None
        self._particles = None
        self._phase_space = None
        self._wake_potential = None
        
    def _get_list(self, group, list_of_elements):
        """
        Will get the group "group" from the hdf5 file and return the children
        of that group given in "list_of_elements" in that order as list
        """
        ret = []
        gr = self.file.get(group)
        for elem in list_of_elements:
            ret.append(gr.get(elem))
        return ret
        
    @property
    def energy_spread(self):
        if self._energy_spread is None:
            self._energy_spread = [self.file.get("EnergySpread").get("axis0"),
                                   self.file.get("EnergySpread").get("data")]
        return self._energy_spread
    
    @property
    def bunch_length(self):
        if self._bunch_length is None:
            self._bunch_length = [self.file.get("BunchLength").get("axis0"),
                                  self.file.get("BunchLength").get("data")]
        return self._bunch_length
    
    @property
    def bunch_position(self):
        if self._bunch_position is None:
            self._bunch_position = [self.file.get("BunchPosition").get("axis0"),
                                    self.file.get("BunchPosition").get("data")]
        return self._bunch_position
    
    @property
    def bunch_population(self):
        if self._bunch_population is None:
            self._bunch_population = self._get_list("BunchPopulation", ["axis0", "data"])
        return self._bunch_population
    
    @property
    def bunch_profile(self):
        if self._bunch_profile is None:
            self._bunch_profile = self._get_list("BunchProfile", ["axis0", "axis1", "data"])
        return self._bunch_profile

    @property
    def csr_intensity(self):
        if self._csr_intensity is None:
            self._csr_intensity = self._get_list("CSR/Intensity", ["axis0", "data"])
        return self._csr_intensity
    
    @property
    def csr_spectrum(self):
        if self._csr_spectrum is None:
            self._csr_spectrum = self._get_list("CSR/Spectrum", ["axis0", "axis1", "data"])
        return self._csr_spectrum
    
    @property
    def energy_profile(self):
        if self._energy_profile is None:
            self._energy_profile = self._get_list("EnergyProfile", ["axis0", "axis1", "data"])
        return self._energy_profile

    @property
    def impedance(self):
        if self._impedance is None:
            self._impedance = self._get_list("Impedance", ["axis0", "data/real", "data/imag"])
        return self._impedance
    
    @property
    def particles(self):
        if self._particles is None:
            self._particles = self._get_list("Particles", ["axis0", "data"])
        return self._particles
    
    @property
    def phase_space(self):
        if self._phase_space is None:
            self._phase_space = self._get_list("PhaseSpace", ["axis0", "axis1", "data"])
        return self._phase_space
    
    @property
    def wake_potential(self):
        if self._wake_potential is None:
            self._wake_potential = self._get_list("WakePotential", ["axis0", "data"])
        return self._wake_potential
            
    @property
    def parameters(self):
        return self.file.get("Info/Parameters").attrs