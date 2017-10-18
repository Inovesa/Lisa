"""
:Author: Patrick Schreiber
"""

from .internals import config_options, lisa_print

if config_options.get("use_cython"):
    try:
        from .file_cython import File
    except ImportError as e:
        print(e)
        print("Fallback to python version")
        from .file import File
else:
    from .file import File
from .internals import lisa_print
from .utils import attr_from_unit, UnitError
import numpy as np

class Data(object):
    """
    Get Data from Inovesa Result Datafiles with specified unit.

    Use the same attributes that are available for Lisa.File objects.

    Usage::

      d = Lisa.Data("/path/to/file")
      d.bunch_profile(2, unit="c")  # 2 for data and unit="c" for coulomb

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
        :param idx: the index of the returned list by File objects. If idx is str the h5 objects are searched for a matching name.
        :param string unit: Use this as second argument or kwarg
        :param sub_idx: (kwarg) the index in the h5object (if File returns [Dataset1, Dataset2] then idx=0 and sub_idx is given will result in Dataset1[sub_idx]) This will speed up if only part of the data is used.
        """
        if attr.endswith("_raw"):
            """
            Return the raw data from File object
            """
            return getattr(self._file, attr[:-4])
        if attr not in self._file._met2gr:
            raise AttributeError("Data object (and File object) does not have an attribute "+attr)
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
            conversion_attribute = attr_from_unit(unit, self.version)

            if kwargs.get("sub_index", None) is not None:
                if 'sub_idx' in kwargs:
                    raise AssertionError("sub_idx or sub_index are to be used, not both")
                kwargs['sub_idx'] = kwargs.pop("sub_index")

            if conversion_attribute is None:
                if kwargs.get("sub_idx", None) is None:
                    return data * np.float64(1.0)
                else:
                    return data[kwargs.get("sub_idx")] * np.float64(1.0)
            else:
                if attr == "impedance" and conversion_attribute not in data.attrs:
                    attrs = self._file.impedance("datagroup").attrs
                else:
                    attrs = data.attrs

            if conversion_attribute in attrs:
                if kwargs.get("sub_idx", None) is None:
                    return data*attrs[conversion_attribute]
                else:
                    return data[kwargs.get("sub_idx")] * attrs[conversion_attribute]
            else:
                lisa_print("units for this data", list(attrs))
                raise UnitError(unit+" is not a valid unit for this data.")
        inner.__doc__ = self.__getattr__.__doc__
        inner.__name__ = attr
        return inner
