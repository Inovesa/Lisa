from .file import File,  FileDataRegister
from .internals import lisa_print
import numpy as np

class UnitError(Exception):
    pass

class Data(object):
    def __init__(self, p_file):
        """
        :param p_file: either a filename of a Lisa.File object
        """
        if isinstance(p_file, File):
            self._file = p_file
        else:
            self._file = File(p_file)

        self._unit_map = {}
        self._build_complete_unit_map()

    def __getattr__(self, attr):
        if attr.endswith("_raw"):
            """
            Return the raw data from File object
            """
            return getattr(self._file, attr[:-4])
        if attr not in FileDataRegister.registered_properties:
            raise AttributeError("Data object (and File object) does not have an attribute "+attr)
        if attr == 'parameters':
            def inner(what):
                if what == 'all':
                    return getattr(self._file, attr)
                else:
                    return getattr(self._file, attr)[what]
            return inner
        def inner(idx, *args, **kwargs):
            """
            Convert to correct unit.
            :param idx: the index of the returned list by File objects
            Use a string for the desired unit either as second argument or as kwarg unit="unitname"
            """
            unit = ''
            if len(args) > 0 and isinstance(args[0], str):
                unit = args[0]
            if 'unit' in kwargs:
                unit = kwargs.get('unit')
            unit = unit.lower() if unit is not None else None
            lisa_print("using unit specification", unit)
            if unit == '':
                raise UnitError("No unit given.")
            elif unit not in self._unit_map and unit is not None:
                lisa_print("possible units", self._unit_map.keys())
                raise UnitError(unit+" is not a valid unit.")
            data = getattr(self._file, attr)[idx]
            if unit is None or self._unit_map[unit] is None:  # do not modify
                # TODO: Check if this is valid for the given data
                return data * np.float64(1.0)
            if self._unit_map[unit] in data.attrs:
                return data*data.attrs[self._unit_map[unit]]
            else:
                lisa_print("units for this data", list(data.attrs))
                raise UnitError(unit+" is not a valid unit for this data.")
        return inner

    def _build_complete_unit_map(self):
        unit_to_attr_map = {
            "m": "Factor4Meters",
            "s": "Factor4Seconds",
            "ts": None,
            "W": "Factor4Watts",
            "A": "Factor4Ampere",
            "C": "Factor4Coulomb",
            "Hz": "Factor4Hertz",
            "eV": "Factor4ElectronVolts"
        }
        alias_map = {
            "m": ["meter", "meters"],
            "s": ["second", "seconds"],
            "ts": ["syncperiods","periods", "synchrotron periods"],
            "W": ["watt", "watts"],
            "A": ["ampere", "amperes"],
            "C": ["coulomb", "coulombs"],
            "Hz": ["hertz"],
            "eV": ["electron volts", "electronvolts", "electron volt", "electron volts"]
        }
        for unit, attr in unit_to_attr_map.items():
            self._unit_map[unit.lower()] = attr
            for alias in alias_map[unit]:
                self._unit_map[alias.lower()] = attr
