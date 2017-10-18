from unittest_helpers import CustomTestCase
import os

import Lisa

s = Lisa.Axis


class TestData(CustomTestCase):
    def setUp(self):
        self.file = Lisa.File(os.path.join(os.path.dirname(__file__), "data", "v15-1.h5"))
        self.data = Lisa.Data(self.file)
        self.units = {"m": "Meter", "s": "Second", "ts": None, "W": "Watt",
                      "ApNES": "AmperePerNES", "CpNES": "CoulombPerNES",
                      "ApNBL": "AmperePerNBL", "CpNBL": "CoulombPerNBL", "V": "Volt",
                      "Hz": "Hertz", "eV": "ElectronVolt", "Ohm": "Ohm", "A": "Ampere", "C": "Coulomb",
                      "ApNBLpNES": "AmperePerNBLPerNES", "CpNBLpNES": "CoulombPerNBLPerNES", "WpHz": "WattPerHertz"}
        self.specs = {
            "BunchLength": {s.TIME: ["s"], s.DATA: ["s", "m"]},
            "BunchPopulation": {s.TIME:["s"], s.DATA: ["A", "C"]},
            "BunchPosition": {s.TIME:["s"], s.DATA:["s", "m"]},
            "BunchProfile": {s.TIME: ["s"], s.XAXIS:["s", "m"], s.DATA:["CpNBL", "ApNBL"]},
            "CSR/Intensity": {s.TIME:["s"], s.DATA: ["W"]},
            "CSR/Spectrum": {s.TIME:["s"], s.FAXIS:["Hz"], s.DATA: ["WpHz"]},
            "EnergyProfile": {s.TIME: ["s"], s.EAXIS:["eV"], s.DATA:["ApNES", "CpNES"]},
            "EnergySpread": {s.TIME: ["s"], s.DATA: ["eV"]},
            "Impedance": {s.FAXIS: ["Hz"], s.REAL:["Ohm"], s.IMAG:["Ohm"], "datagroup":[]},
            "Particles": {s.TIME: ["s"], s.DATA: []},
            "WakePotential": {s.TIME: ["s"], s.XAXIS: ["s", "m"], s.DATA: ["V"]},
            "PhaseSpace": {s.TIME: ["s"], s.XAXIS: ["s", "m"], s.EAXIS: ["eV"], s.DATA: ["ApNBLpNES", "CpNBLpNES"]},
            "SourceMap": {s.XAXIS:["s", "m"], s.EAXIS: ["eV"], s.XDATA: [], s.YDATA:[]}
        }

    def test_conversion(self):
        for data in self.file._met2gr:
            if data == "parameters": continue
            for axis, units in self.specs[self.file._met2gr[data]].items():
                for unit in units:
                    with self.subTest(msg=data, axis=axis, unit=unit):
                        factor = getattr(self.file, data)(axis).attrs[self.units[unit]] if axis not in ["imag", "real"] \
                            else getattr(self.file, data)('datagroup').attrs[self.units[unit]]
                        mandata = getattr(self.file, data)(axis) * factor
                        self.assertListEqual(getattr(self.data, data)(axis, unit=unit).tolist(), mandata.tolist())

