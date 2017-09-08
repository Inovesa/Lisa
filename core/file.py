# -*- coding: utf-8 -*-
"""
:Author: Patrick Schreiber
"""

import h5py as h5
import glob
import numpy as np

from .utils import InovesaVersion, version14, version15

class FileDataRegister():
    registered_properties = []


class AttributedNPArray(np.ndarray):
    """Simple Wrarpper around numpy.ndarray to include h5 attrs attribute"""
    def __new__(cls, orig_arr, attrs, name):
        obj = np.asarray(orig_arr).view(cls)
        obj.attrs = attrs
        obj.name = name
        return obj
    def __array_finalize__(self, obj):
        if obj is None: return
        self.attrs = getattr(obj, 'attrs', None)
        self.name = getattr(obj, 'name', None)



def registered(cls):
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
        cls.registered_properties.append(func.__name__)
        return func
    return wrapper


class AxisSelector(object):
    TIME = "timeaxis"
    XAXIS = "spaceaxis"
    EAXIS = "energyaxis"
    FAXIS = "frequencyaxis"
    DATA = "data"
    REAL = "real"
    IMAG = "imag"
    def __init__(self):
        self._specs = {
            "BunchLength": [self.TIME, self.DATA],
            "BunchPopulation": [self.TIME, self.DATA],
            "BunchPosition": [self.TIME, self.DATA],
            "BunchProfile": [self.TIME, self.XAXIS, self.DATA],
            "CSR/Intensity": [self.TIME, self.DATA],
            "CSR/Spectrum": [self.TIME, self.FAXIS],
            "EnergyProfile": [self.TIME, self.EAXIS, self.DATA],
            "EnergySpread": [self.TIME, self.DATA],
            "Impedance": [self.FAXIS, self.REAL, self.IMAG, "datagroup"],
            "Particles": [self.TIME, self.DATA],
        }
        self._axis_datasets = {
            self.TIME: "/Info/AxisValues_t",
            self.XAXIS: "/Info/AxisValues_z",
            self.EAXIS: "/Info/AxisValues_E",
            self.FAXIS: "/Info/AxisValues_f"
        }
        self._data_datasets = {
            self.DATA: "data",
            self.REAL: "data/real",
            self.IMAG: "data/imag",
            "datagroup": "data"
        }

    def all_for(self, group):
        return self._specs[group]

    def __call__(self, axis, group):  # csr_spectrum has swapped axis in versions below 0.15
        if axis not in self._specs[group]:
            raise ValueError("'"+axis+"' is not in group '"+group+"'")
        return self._axis_datasets.get(axis, self._data_datasets.get(axis))  # if nto in axis_datasets get it from _data_datasets

Axis = AxisSelector


class DataContainer(object):
    def __new__(cls, data_dict, list_of_elements):
        if len(list_of_elements) == 1:  # if only one element then do not bother with DataContainer but return h5 object
            return data_dict[list_of_elements[0]]
        else:
            return super(DataContainer, cls).__new__(cls)

    def __init__(self, data_dict, list_of_elements):
        self._data_dict = data_dict
        self._list_of_elements = list_of_elements

    def __getitem__(self, name):
        if isinstance(name, int):
            return self._data_dict[self._list_of_elements[name]]
        if name in self._data_dict:
            return self._data_dict[name]
        else:
            raise ValueError("'"+name+"' not in this Container")

    def __getattr__(self, item):
        return self[item]

    def __len__(self):
        return len(self._list_of_elements)


class File(object):
    """
    Wrapper around a h5 File created by Inovesa
    """
    def __init__(self, filename):
        """
        Create File object
        :param filename: The filename of the Inovesa result file
        """
        self.filename = filename
        self.file = h5.File(filename, 'r')
        self._data = {}

        try:
            self.version = InovesaVersion(*self.file.get("Info").get("Inovesa_v"))
        except TypeError:
            self.version = InovesaVersion(*self.file.get("Info").get("INOVESA_v"))

        self.select_axis = AxisSelector()

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

    def _get_dict(self, group, list_of_elements):
        """
        Will get the group "group" from the hdf5 file and save it to self._data[key]
        """
        dg = self._data.setdefault(group, {})
        if len(list_of_elements) == 0:
            list_of_elements = self.select_axis.all_for(group)
        set_of_new_elements = set(list_of_elements) - set(dg.keys())  # filter might be faster
        if len(set_of_new_elements) != 0:
            gr = self.file.get(group)
            for elem in set_of_new_elements:
                ax = self.select_axis(elem, group)
                dg[elem] = gr.get(ax)
        return DataContainer(dg, list_of_elements)

    def preload_full(self, what):
        """
        Preload Data into memory. This will speed up recurring reads by a lot
        """
        try:
            h5data = getattr(self, what)
            tmp = [np.zeros(i.shape, dtype=i.dtype) for i in h5data]
            sdata = [i.read_direct(tmp[idx]) for idx, i in enumerate(h5data)]
            sdata = [AttributedNPArray(tmp[idx], i.attrs, i.name) for idx, i in enumerate(h5data)]
            setattr(self, "_"+what, sdata)
        except:
            print("Error")

    def _sub_element(self, what, sub):
        if isinstance(sub, int):
            return self._data[what][sub]
        elif isinstance(sub, str):
            if sub in self._data[what]:
                return self._data[what][sub]
            else:
                pd = list(filter(lambda x: sub in x.name, self._data[what].values()))
                if len(pd) > 1:
                    raise IndexError("'%s' was not found or was found multiple times."%str(sub))
                else:
                    return pd[0]
        else:
            raise IndexError("'%s' is not a valid index and no matching element was found."%str(sub))

    @registered(FileDataRegister)
    def energy_spread(self, *selectors):
        """
        Return the EnergySpread
        """
        return self._get_dict("EnergySpread", selectors)

    @registered(FileDataRegister)
    def bunch_length(self, *selectors):
        """
        Return the BunchLength
        """
        return self._get_dict("BunchLength", selectors)

    @registered(FileDataRegister)
    def bunch_position(self, *selectors):
        """
        Return the BunchPosition
        """
        return self._get_dict("BunchPosition", selectors)

    @registered(FileDataRegister)
    def bunch_population(self, *selectors):
        """
        Return the BunchPopulation
        """
        return self._get_dict("BunchPopulation", selectors)

    @registered(FileDataRegister)
    def bunch_profile(self, *selectors):
        """
        Return the BunchProfile
        :return: [BunchProfile.axis0, BunchProfile.axis1, BunchProfile.data]
        """
        return self._get_dict("BunchProfile", selectors)

    @registered(FileDataRegister)
    def csr_intensity(self, *selectors):
        """
        Return the CSRIntensity
        """
        return self._get_dict("CSR/Intensity", selectors)

    @registered(FileDataRegister)
    def csr_spectrum(self, *selectors):
        """
        Return the CSRSpectrum
        """
        return self._get_dict("CSR/Spectrum", selectors)

    @registered(FileDataRegister)
    def energy_profile(self, *selectors):
        """
        Return the EnergyProfile
        """
        return self._get_dict("EnergyProfile", selectors)

    @registered(FileDataRegister)
    def impedance(self, *selectors):
        """
        Return the Impedance
        """
        return self._get_dict("Impedance", selectors)

    @registered(FileDataRegister)
    def particles(self, *selectors):
        """
        Return the Particles
        """
        return self._get_dict("Particles", selectors)

    @registered(FileDataRegister)
    def phase_space(self, *selectors):
        """
        Return the PhaseSpace
        """
        return self._get_dict("PhaseSpace", selectors)

    @registered(FileDataRegister)
    def wake_potential(self, *selectors):
        """
        Return the WakePotential
        """
        return self._get_dict("WakePotential", selectors)

    @registered(FileDataRegister)
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
