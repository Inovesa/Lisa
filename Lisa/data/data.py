"""
:Author: Patrick Schreiber
"""

from ..internals import config_options

if config_options.get("use_cython"):
    try:
        from .file_cython import File, Axis
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .file import File, Axis
else:
    from .file import File, Axis
from ..internals import lisa_print
from .utils import attr_from_unit, UnitError, DataNotInFile
import numpy as np


class Data(object):
    """
    Get Data from Inovesa Result Datafiles with specified unit.

    Use the same attributes that are available for Lisa.File objects.

    Usage::

      d = Lisa.Data("/path/to/file")
      d.bunch_profile(Lisa.Axis.DATA, unit="c")  # unit="c" for coulomb
      d.bunch_profile(Lisa.Axis.XAXIS, unit="s")  # unit="s" for second XAXIS for space axis

    .. seealso:: Lisa.File
    """
    def __init__(self, p_file):
        """
        :param p_file: either a filename of a Lisa.File object
        """
        if isinstance(p_file, File):
            self._file = p_file
        else:
            self._file = File(p_file)

        self.version = self._file.version

    def __getattr__(self, attr):
        """
        Convert to correct unit.
        :param idx: An axis specification from Lisa.Axis
        :param string unit: Use this as second argument or kwarg
        :param sub_idx: (kwarg) the index in the h5object (if File returns [Dataset1, Dataset2]
        then idx=0 and sub_idx is given will result in Dataset1[sub_idx])
        This will speed up if only part of the data is used.
        """
        if attr.endswith("_raw"):
            """
            Return the raw data from File object
            """
            return getattr(self._file, attr[:-4])
        if attr not in self._file._met2gr:
            try:
                return self.__getattribute__(attr)
            except AttributeError:
                if attr.startswith("__") and attr.endswith("__"):
                    raise AttributeError("'Data' object has no attribute '" + attr + "'")
                raise DataNotInFile("Data object (and File object) does not have an attribute " +
                                    attr)
        if attr == 'parameters':
            def inner(what):
                if what == 'all':
                    return getattr(self._file, attr)()
                else:
                    return getattr(self._file, attr)()[what]
            return inner

        def inner(idx, *args, **kwargs):
            unit = ''
            if len(args) > 0 and isinstance(args[0], str):
                unit = args[0]
            if 'unit' in kwargs:
                unit = kwargs.get('unit')
            unit = unit.lower() if unit is not None else None
            lisa_print("using unit specification", unit)
            if unit == '':
                raise UnitError("No unit given.")
            data = getattr(self._file, attr)(idx)

            sub_index = kwargs.get("sub_index", kwargs.get("sub_idx", None))

            factor = self._conversion_factor(unit, attr, data)

            if factor is None:
                if sub_index is None:
                    return data * np.float64(1.0)
                else:
                    return data[sub_index] * np.float64(1.0)
            if sub_index is None:
                return data * factor
            else:
                return data[sub_index] * factor

        inner.__doc__ = self.__getattr__.__doc__
        inner.__name__ = attr
        return inner

    def _conversion_factor(self, unit, attr, data):
        """
        Get the conversion factor for unit for attr from data
        :param unit: The physical unit to use (lowercase!)
        :param attr: The attribute (the data e.g. bunch_profile)
        :param data: The actual data (h5 object) to extract the conversion factor from
        :return: float, conversion_factor
        """
        if unit is None:
            return None
        unit_lst = ["cps", "c/s", "aps", "a/s"]
        if unit in unit_lst:
            if Axis.EAXIS in self._file.select_axis.all_for(attr):
                raise UnitError("Illegal conversion")
            try:
                coa = attr_from_unit(unit[0] + "pnbl", self.version)
                coa = getattr(self._file, attr)(Axis.DATA).attrs[coa]
                s = attr_from_unit("s", self.version)
                s = getattr(self._file, attr)(Axis.XAXIS).attrs[s]
                return coa / s
            except (KeyError, DataNotInFile) as e:
                if isinstance(e, KeyError):
                    raise UnitError("Conversion failure, cannot find attribute for " +
                                    str(e).split("'")[-2])
                else:
                    raise UnitError("Illegal conversion, "
                                    "corresponding data objects not found in h5. " + str(e))
        unit_lst = ["c/ev", "cpev", "a/ev", "apev"]
        if unit in unit_lst:
            if Axis.XAXIS in self._file.select_axis.all_for(attr):
                raise UnitError("Illegal conversion")
            try:
                coa = attr_from_unit(unit[0] + "pnes", self.version)
                coa = getattr(self._file, attr)(Axis.DATA).attrs[coa]
                ev = attr_from_unit("eV", self.version)
                ev = getattr(self._file, attr)(Axis.EAXIS).attrs[ev]
                return coa / ev
            except (KeyError, DataNotInFile) as e:
                if isinstance(e, KeyError):
                    raise UnitError("Conversion failure, cannot find attribute for " +
                                    str(e).split("'")[-2])
                else:
                    raise UnitError("Illegal conversion, "
                                    "corresponding data objects not found in h5. " + str(e))
        unit_lst = ["cpspev", "c/s/ev", "apspev", "a/s/ev", "cpevps", "c/ev/s", "apevps", "a/ev/s"]
        if unit in unit_lst:
            try:
                coa = attr_from_unit(unit[0] + "pnblpnes", self.version)
                coa = getattr(self._file, attr)(Axis.DATA).attrs[coa]
                ev = attr_from_unit("eV", self.version)
                ev = getattr(self._file, attr)(Axis.EAXIS).attrs[ev]
                s = attr_from_unit("s", self.version)
                s = getattr(self._file, attr)(Axis.XAXIS).attrs[s]
                return coa / ev / s
            except (KeyError, DataNotInFile) as e:
                if isinstance(e, KeyError):
                    raise UnitError("Conversion failure, cannot find attribute for " +
                                    str(e).split("'")[-2])
                else:
                    raise UnitError("Illegal conversion, "
                                    "corresponding data objects not found in h5. " + str(e))

        conversion_attribute = attr_from_unit(unit, self.version)
        if conversion_attribute is None:
            return None
        if attr == "impedance" and conversion_attribute not in data.attrs:
            attrs = self._file.impedance("datagroup").attrs
        else:
            attrs = data.attrs
        if conversion_attribute in attrs:
            return attrs[conversion_attribute]
        elif conversion_attribute.startswith("Factor4") and conversion_attribute[7:] in attrs:
            # for some versions of v14-1
            return attrs[conversion_attribute[7:]]
        elif conversion_attribute.startswith("Factor4") and conversion_attribute[7:-1] in attrs:
            # for some versions of v14-1
            return attrs[conversion_attribute[7:-1]]
        else:
            lisa_print("units for this data", list(attrs))
            raise UnitError(unit + " is not a valid unit for this data.")

    def unit_factor(self, data, axis, unit):
        """
        Get the factor to calculate values in the correct physical unit
        :param data: The data to get the factor for (e.g. bunch_profile)
        :param axis: The Axis object to select what axis to get the factor for
        :param unit: The actual unit
        :return: Factor to get the data in physical units (physical=data*factor)
        """
        if not isinstance(unit, str):
            raise UnitError("Unit has to be string object")
        unit = unit.lower()
        data_object = getattr(self._file, data)(axis)
        return self._conversion_factor(unit, data, data_object)
