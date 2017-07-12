# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 13:19:04 2017

@author: patrick
"""

import h5py as h5
import glob
import numpy as np

class FileDataRegister():
    registered_properties = []


class AttributedNPArray(np.ndarray):
    def __new__(cls, orig_arr, attrs):
        obj = np.asarray(orig_arr).view(cls)
        obj.attrs = attrs
        return obj
    def __array_finalize__(self, obj):
        if obj is None: return
        self.attrs = getattr(obj, 'attrs', None)


def registered_property(cls):
    """
    Registeres properties of one class into another class.registered_properties
    """
    if hasattr(cls, 'registered_properties'):
        if hasattr(cls, 'registered_properties'):
            if not isinstance(cls.registered_properties, list):
                raise AttributeError(cls.__name__+" has attribute registered_properties of wrong type.")
        else:
            cls.registered_properties = []
    def wrapper(func):
        # if func.__name__ not in cls.registered_properties:  ## Use this if stuff turns up multiple times
        cls.registered_properties.append(func.__name__)
        p = property(func)
        p.__doc__ = func.__doc__
        return p
    return wrapper

class File(object):
    """Wrapper around a h5 File created by Inovesa"""
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

    def preload_full(self, what):
        """
        Preload Data into memory. This will speed up recurring reads by a lot
        """
        try:
            h5data = getattr(self, what)
            tmp = [np.zeros(i.shape, dtype=i.dtype) for i in h5data]
            sdata = [i.read_direct(tmp[idx]) for idx, i in enumerate(h5data)]
            sdata = [AttributedNPArray(tmp[idx], i.attrs) for idx, i in enumerate(h5data)]
            setattr(self, "_"+what, sdata)
        except:
            print("Error")

    @registered_property(FileDataRegister)
    def energy_spread(self):
        """
        Return the EnergySpread
        :return: [EnergySpread.axis0, EnergySpread.data]
        """
        if self._energy_spread is None:
            self._energy_spread = [self.file.get("EnergySpread").get("axis0"),
                                   self.file.get("EnergySpread").get("data")]
        return self._energy_spread

    @registered_property(FileDataRegister)
    def bunch_length(self):
        """
        Return the BunchLength
        :return: [BunchLength.axis0, BunchLength.data]
        """
        if self._bunch_length is None:
            self._bunch_length = [self.file.get("BunchLength").get("axis0"),
                                  self.file.get("BunchLength").get("data")]
        return self._bunch_length

    @registered_property(FileDataRegister)
    def bunch_position(self):
        """
        Return the BunchPosition
        :return: [BunchPosition.axis0, BunchPosition.data]
        """
        if self._bunch_position is None:
            self._bunch_position = [self.file.get("BunchPosition").get("axis0"),
                                    self.file.get("BunchPosition").get("data")]
        return self._bunch_position

    @registered_property(FileDataRegister)
    def bunch_population(self):
        """
        Return the BunchPopulation
        :return: [BunchPopulation.axis0, BunchPopulation.data]
        """
        if self._bunch_population is None:
            self._bunch_population = self._get_list("BunchPopulation", ["axis0", "data"])
        return self._bunch_population

    @registered_property(FileDataRegister)
    def bunch_profile(self):
        """
        Return the BunchProfile
        :return: [BunchProfile.axis0, BunchProfile.axis1, BunchProfile.data]
        """
        if self._bunch_profile is None:
            self._bunch_profile = self._get_list("BunchProfile", ["axis0", "axis1", "data"])
        return self._bunch_profile

    @registered_property(FileDataRegister)
    def csr_intensity(self):
        """
        Return the CSRIntensity
        :return: [CSRIntensity.axis0, CSRIntensity.axis1, CSRIntensity.data]
        """
        if self._csr_intensity is None:
            self._csr_intensity = self._get_list("CSR/Intensity", ["axis0", "data"])
        return self._csr_intensity

    @registered_property(FileDataRegister)
    def csr_spectrum(self):
        """
        Return the CSRSpectrum
        :return: [CSRSpectrum.axis0, CSRSpectrum.axis1, CSRSpectrum.data]
        """
        if self._csr_spectrum is None:
            self._csr_spectrum = self._get_list("CSR/Spectrum", ["axis0", "axis1", "data"])
        return self._csr_spectrum

    @registered_property(FileDataRegister)
    def energy_profile(self):
        """
        Return the EnergyProfile
        :return: [EnergyProfile.axis0, EnergyProfile.axis1, EnergyProfile.data]
        """
        if self._energy_profile is None:
            self._energy_profile = self._get_list("EnergyProfile", ["axis0", "axis1", "data"])
        return self._energy_profile

    @registered_property(FileDataRegister)
    def impedance(self):
        """
        Return the Impedance
        :return: [Impedance.axis0, Impedance.real, Impedance.imag]
        """
        if self._impedance is None:
            self._impedance = self._get_list("Impedance", ["axis0", "data/real", "data/imag"])
        return self._impedance

    @registered_property(FileDataRegister)
    def particles(self):
        """
        Return the Particles
        :return: [Particles.axis0, Particles.data]
        """
        if self._particles is None:
            self._particles = self._get_list("Particles", ["axis0", "data"])
        return self._particles

    @registered_property(FileDataRegister)
    def phase_space(self):
        """
        Return the PhaseSpace
        :return: [PhaseSpace.axis0, PhaseSpace.axis1 ,PhaseSpace.data]
        """
        if self._phase_space is None:
            self._phase_space = self._get_list("PhaseSpace", ["axis0", "axis1", "data"])
        return self._phase_space

    @registered_property(FileDataRegister)
    def wake_potential(self):
        """
        Return the WakePotential
        :return: [WakePotential.axis0, WakePotential.data]
        """
        if self._wake_potential is None:
            self._wake_potential = self._get_list("WakePotential", ["axis0", "data"])
        return self._wake_potential

    @registered_property(FileDataRegister)
    def parameters(self):
        """
        Return the Inovesa Parameters
        :return: h5py.Attribute Instance
        """
        return self.file.get("Info/Parameters").attrs


class MultiFile(object):
    """
    Multiple File container for whole directories
    """
    def __init__(self, path, pattern=None, sorter=None):
        """
        :param path: The path to search in
        :param pattern: The pattern to search for (pattern has to be accepted by glob) (None for no pattern)
        :param sorter: The sorting method to use. (None for default)
        """
        self.path = path
        self.pattern = pattern
        self.sorter = sorter
        self._sort_changed = True
        self._filelist = []
        self._sorted_filelist = []
        self._fileobjectlist = []
        self._generate_file_list_()

    @classmethod
    def _get_current_from_cfg(cls, filename):
        with open(filename+".cfg", 'r') as f:
            for line in f:
                if line.startswith("BunchCurrent"):
                    return float(line.split("=")[1])

    def _generate_file_list_(self):
        self._filelist = glob.glob(self.path+"/"+(self.pattern if self.pattern is not None else "*"))
        self._sorted_filelist = self._filelist  # put files in sorted_filelist even if not sorted

    def _sort_file_list(self):
        if self.sorter is not None and hasattr(self.sorter, "__call__"):
            self._sorted_filelist = self.sorter(self._filelist)
        else:
            tmp_list = []
            for file in self._filelist:
                tmp_list.append((MultiFile._get_current_from_cfg(file), file))
            tmp_list.sort(key=lambda f: f[0], reverse=True)  # make sure it is sorted by the first entry
            self._sorted_filelist = [i[1] for i in tmp_list]

    def set_sorter(self, sorter):
        """
        Set the sorting method
        :param sorter: A callable that accepts a list of files as strings and returns a sorted list of strings
        """
        self.sorter = sorter
        self._sort_changed = True


    def strlst(self, sorted=True):
        """
        Get File list as string list
        :param sorted: True to sort the list
        """
        if sorted:
            if self._sort_changed:
                self._sort_file_list()
            return self._sorted_filelist
        else:
            return self._filelist

    def objlst(self, sorted=True):
        """
        Get File list as Lisa.File object list
        :param sorted: True to sort the list
        """
        if sorted:
            if self._sort_changed:
                self._sort_file_list()
        if len(self._fileobjectlist) == 0:
            for file in self._sorted_filelist:
                self._fileobjectlist.append(File(file))
        return self._fileobjectlist
