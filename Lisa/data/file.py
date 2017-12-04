# -*- coding: utf-8 -*-
"""
:Author: Patrick Schreiber
"""

import glob

import h5py as h5
import numpy as np

from .utils import InovesaVersion, version13_0, \
    version9_1, DataNotInFile


class FileDataRegister(object):
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
    XDATA = "xdata"
    YDATA = "ydata"

    def __init__(self, version):
        self._version = version
        self._specs = {
            "bunch_length": [self.TIME, self.DATA],
            "bunch_population": [self.TIME, self.DATA],
            "bunch_position": [self.TIME, self.DATA],
            "bunch_profile": [self.TIME, self.XAXIS, self.DATA],
            "csr_intensity": [self.TIME, self.DATA],
            "csr_spectrum": [self.TIME, self.FAXIS, self.DATA],
            "energy_profile": [self.TIME, self.EAXIS, self.DATA],
            "energy_spread": [self.TIME, self.DATA],
            "impedance": [self.FAXIS, self.REAL, self.IMAG, "datagroup"],
            "particles": [self.TIME, self.DATA],
            "wake_potential": [self.TIME, self.XAXIS, self.DATA],
            "phase_space": [self.TIME, self.XAXIS, self.EAXIS, self.DATA]
        }

        if version > version13_0:
            self._specs["source_map"] = [self.XAXIS, self.EAXIS, self.XDATA, self.YDATA]

        self._axis_datasets = {
            self.TIME: "/Info/AxisValues_t",
            self.XAXIS: "/Info/AxisValues_z",
            self.EAXIS: "/Info/AxisValues_E",
            self.FAXIS: "/Info/AxisValues_f"
        }
        self._data_datasets = {
            self.DATA: "data",
            self.REAL: "data/real",  # Impedance
            self.IMAG: "data/imag",  # Impedance
            self.XDATA: "data/x",  # SourceMap
            self.YDATA: "data/y",  # SourceMap
            "datagroup": "data"
        }

    def all_for(self, group):
        return self._specs[group]

    def __call__(self, axis, group):
        if group not in self._specs:
            raise DataNotInFile("'{gr}' is not in a valid dataset".format(gr=group))
        if axis not in self._specs[group]:
            raise DataNotInFile("'{ax}' is not in group '{gr}'".format(ax=axis, gr=group))
        return self._axis_datasets.get(axis, self._data_datasets.get(axis))  # if nto in axis_datasets get it from _data_datasets


Axis = AxisSelector


class DataError(Exception):
    pass


class DataContainer(object):
    def __new__(cls, data_dict, list_of_elements):
        if len(list_of_elements) == 1:  # if only one element then do not bother with DataContainer but return h5 object
            try:
                return data_dict[list_of_elements[0]]
            except:
                raise DataError("Tried to access unavailable elements.")
        else:
            return super(DataContainer, cls).__new__(cls)

    def __init__(self, data_dict, list_of_elements):
        if not all([l in data_dict for l in list_of_elements]):
            raise DataError("Tried to access unavailable elements.")
        self._data_dict = data_dict
        self._list_of_elements = list_of_elements

    def __getitem__(self, name):
        if isinstance(name, int):
            return self._data_dict[self._list_of_elements[name]]
        if name in self._data_dict:
            return self._data_dict[name]
        else:
            raise DataError("'"+name+"' not in this Container")

    def __contains__(self, item):
        return item in self._list_of_elements

    def __getattr__(self, item):
        return self[item]

    def get(self, item, default):
        try:
            return self[item]
        except ValueError:
            return default

    def __len__(self):
        return len(self._list_of_elements)

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        self.idx += 1
        if self.idx == len(self._list_of_elements):
            raise StopIteration
        return self._list_of_elements[self.idx-1], self._data_dict[self._list_of_elements[self.idx-1]]


class File(object):
    """
    Wrapper around a h5 File created by Inovesa

    Each Datagroup is a method of this object. To get a special axis of each group use additional parameters.

    If one parameter is supplied the data will be returned as HDF5.Dataset object or, if preloaded, as AttributedNPArray.

    If no or more than one parameter is supplied the data will be returned as DataContainer object containing
    the HDF5.Dataset or AttributedNPArray objects.

    This is not completely true for File.parameters.

    ::

        f = File("path/to/file")
        tax = f.bunch_profile(Axis.TIME)
        xax = f.bunch_profile(Axis.XAXIS)
        data = f.bunch_profile(Axis.DATA)
        all = f.bunch_profile()
        axes = f.bunch_profile(Axis.TIME, Axis.XAXIS)

    Method names are mostly the datagroup-names with underscores instead of camelcase (e.g. bunch_profile for BunchProfile)

    Available Groups:

        - energy_spread
        - bunch_length
        - bunch_position
        - bunch_population
        - bunch_profile
        - csr_intensity
        - csr_spectrum
        - energy_profile
        - impedance
        - particles
        - phase_space
        - wake_potential
        - source_map (only Inovesa version 0.15 and above)
        - * parameters

    * parameters does not expose the exact same interface. Use File.parameters() to get the HDF5 Attribute Object.
    Use File.parameters(param1, param2 ...) to get either a single parameter (with the datatype that this parameter is saved
    in the hdf5 file) or a DataContainer object depending on how much params were passed.

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

        self.select_axis = AxisSelector(self.version)

        self._met2gr = {
            "energy_spread": "EnergySpread",
            "bunch_length": "BunchLength",
            "bunch_position": "BunchPosition",
            "bunch_population": "BunchPopulation",
            "bunch_profile": "BunchProfile",
            "csr_intensity": "CSR/Intensity",
            "csr_spectrum": "CSR/Spectrum",
            "energy_profile": "EnergyProfile",
            "impedance": "Impedance",
            "particles": "Particles",
            "phase_space": "PhaseSpace",
            "wake_potential": "WakePotential",
            "parameters": "Info/Parameters"
        }
        if self.version > version13_0:
            self._met2gr.update({"source_map": "SourceMap"})

        if self.version == version9_1:
            self._met2gr.update({"csr_intensity": "CSRPower"})
            self._met2gr.update({"csr_spectrum": "CSRSpectrum"})
            self._met2gr.update({"bunch_population": "BunchCurrent"})
            del self._met2gr["particles"]
            del self._met2gr["parameters"]
            del self._met2gr["energy_profile"]

    def _read_from_cfg(self, what):
        try:
            with open(self.filename[:-3] + ".cfg", 'r') as f:
                for line in f:
                    if line.startswith(what):
                        return float(line.split("=")[1].strip())
        except FileNotFoundError:
            return None

    def _get_dict(self, what, list_of_elements):
        """
        Will get the group "group" from the hdf5 file and save it to self._data[what]
        """
        group = self._met2gr.get(what, None)
        if not group:
            if what in self._met2gr.values():
                group = what
            else:
                raise DataNotInFile("'{}' does not exist in file.".format(what))
        dg = self._data.setdefault(group, {})
        # if no elements or None passed get all
        if len(list_of_elements) == 0 or (len(list_of_elements) == 1 and list_of_elements[0] is None):
            list_of_elements = self.select_axis.all_for(what)
        # check what elements have to be loaded from disk (no real load)
        set_of_new_elements = set(list_of_elements) - set(dg.keys())  # filter might be faster
        if len(set_of_new_elements) != 0:
            gr = self.file.get(group)
            for elem in set_of_new_elements:
                ax = self.select_axis(elem, what)
                if self.version == version9_1:
                    if elem == Axis.TIME:
                        dg[elem] = AttributedNPArray(gr.get(ax)[1:], gr.get(ax).attrs, gr.get(ax).name)
                    elif elem == Axis.DATA and Axis.TIME in self.select_axis.all_for(what):
                        dg[elem] = dg[elem] = AttributedNPArray(gr.get(ax)[1:], gr.get(ax).attrs, gr.get(ax).name)
                    elif elem == Axis.XAXIS or elem == Axis.EAXIS or elem == Axis.FAXIS:
                        dg[elem] = dg[elem] = AttributedNPArray(gr.get(ax)[0], gr.get(ax).attrs, gr.get(ax).name)
                    else:
                        dg[elem] = gr.get(ax)
                else:
                    dg[elem] = gr.get(ax)
        return DataContainer(dg, list_of_elements)

    def preload_full(self, what, axis=None):
        """
        Preload Data into memory. This will speed up recurring reads by a lot
        """
        try:
            h5data = getattr(self, what)(axis)
            tmp = [np.zeros(i.shape, dtype=i.dtype) for _, i in h5data]
            for idx, (name, i) in enumerate(h5data):
                if isinstance(i, h5.Dataset):
                    i.read_direct(tmp[idx])
                    sdata = {name: AttributedNPArray(tmp[idx], i.attrs, i.name)}
                    self._data[self._met2gr[what]].update(sdata)
        except:
            print("Error preloading data")

    def __getattr__(self, what):
        if what not in self._met2gr and what != "parameters":
            try:
                return self.__getattribute__(what)
            except AttributeError:
                if what.startswith("__") and what.endswith("__"):
                    raise AttributeError("'Data' object has no attribute '"+what+"'")
                raise DataNotInFile("'{}' does not exist in file.".format(what))

        def data_getter(*selectors):
            if what == "parameters":
                if len(selectors) == 0:
                    return self.file.get("Info/Parameters").attrs
                else:
                    try:
                        data_dict = {}
                        for sel in selectors:
                            if self.version == version9_1 and sel == "BunchCurrent":
                                value = self._read_from_cfg(sel)
                                if value is None:
                                    value = self.file.get("BunchCurrent/data")[0]
                                data_dict[sel] = value
                            elif self.version == version9_1 and sel == "RevolutionFrequency":
                                data_dict[sel] = self._read_from_cfg(sel)
                            else:
                                data_dict[sel] = self.file.get("Info/Parameters").attrs.get(sel)
                        return DataContainer(data_dict, selectors)
                    except DataError:
                        raise DataNotInFile("One of the parameters is not saved in hdf5 file.")
            else:
                return self._get_dict(what, selectors)
        return data_getter


class File_dep(object):
    """
    Wrapper around an h5 File created by Inovesa
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
        if len(list_of_elements) == 0 or (len(list_of_elements) == 1 and list_of_elements[0] is None):
            list_of_elements = self.select_axis.all_for(group)
        set_of_new_elements = set(list_of_elements) - set(dg.keys())  # filter might be faster
        if len(set_of_new_elements) != 0:
            gr = self.file.get(group)
            for elem in set_of_new_elements:
                ax = self.select_axis(elem, group)
                dg[elem] = gr.get(ax)
        return DataContainer(dg, list_of_elements)

    def preload_full(self, what, axis=None):
        """
        DEPRECATED
        Preload Data into memory. This will speed up recurring reads by a lot
        """
        print("Not fully implemented. Use new version of File")
        return
        try:
            h5data = getattr(self, what)(axis)
            tmp = [np.zeros(i.shape, dtype=i.dtype) for _, i in h5data]
            sdata = [i.read_direct(tmp[idx]) for idx, (_, i) in enumerate(h5data)]
            sdata = {name: AttributedNPArray(tmp[idx], i.attrs, i.name) for idx, (name, i) in enumerate(h5data)}
            # NOTE: This does not work at the moment
            # self._data[self._met2gr[what]].update(sdata)
        except:
            print("Error preloading data")

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
                if isinstance(file, list) or isinstance(file, tuple):
                    self._fileobjectlist.append((File(file[0]), *file[1:]))
                else:
                    self._fileobjectlist.append(File(file))
        return self._fileobjectlist
