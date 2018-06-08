# from unittest_helpers import CustomTestCase
import h5py
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose

# rethink importing it
import Lisa
from Lisa.data.utils import DataNotInFile

s = Lisa.Axis

import os.path as op

import unittest

class FileTest(unittest.TestCase):
    def setUp(self):
        self.file_dir_path = op.join(op.dirname(__file__), "data")
        self.specs = {
            "bunch_length": [s.TIME, s.DATA],
            "bunch_population": [s.TIME, s.DATA],
            "bunch_position": [s.TIME, s.DATA],
            "bunch_profile": [s.TIME, s.XAXIS, s.DATA],
            "csr_intensity": [s.TIME, s.DATA],
            "csr_spectrum": [s.TIME, s.FAXIS, s.DATA],
            "energy_profile": [s.TIME, s.EAXIS, s.DATA],
            "energy_spread": [s.TIME, s.DATA],
            "impedance": [s.FAXIS, s.REAL, s.IMAG, "datagroup"],
            "particles": [s.TIME, s.DATA],
            "wake_potential": [s.TIME, s.XAXIS, s.DATA],
            "phase_space": [s.TIME, s.XAXIS, s.EAXIS, s.DATA]
        }
        self._axis_datasets = {
            s.TIME: "/Info/AxisValues_t",
            s.XAXIS: "/Info/AxisValues_z",
            s.EAXIS: "/Info/AxisValues_E",
            s.FAXIS: "/Info/AxisValues_f"
        }
        self._data_datasets = {
            s.DATA: "data",
            s.REAL: "data/real",  # Impedance
            s.IMAG: "data/imag",  # Impedance
            s.XDATA: "data/x",  # SourceMap
            s.YDATA: "data/y",  # SourceMap
            "datagroup": "data"
        }
        self._blfunc = None

    def do_test(self, file):
        f = file
        for par in self.specs:
            with self.subTest(msg=par):
                obj = getattr(f, par)()
                self.assertIsInstance(obj, Lisa.data.DataContainer)
                self.assertEqual(len(obj), len(self.specs[par]))
                for idx, spec in enumerate(self.specs[par]):
                    with self.subTest(msg=par, spec=spec):
                        # this tests if the correct order is used in DataContainer
                        # To be compatible with multiple inovesa versions we convert this explicitly to a np.array
                        if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                            self.assertEqual(getattr(obj, spec), obj[idx])
                        else:
                            self.assertListEqual(np.array(getattr(obj, spec)).tolist(), np.array(obj[idx]).tolist())
                for spec in self.specs[par]:  # test for axis and data
                    if spec == "datagroup":  # skip because only in impedance and REAL and IMAG get tested individually anyway
                        continue 

                    with self.subTest(msg=par, spec_type=spec):
                        obj = getattr(f, par)(spec)
                        if spec in self._axis_datasets:  # Check for Axis data
                            if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                                self.assertEqual(obj, f.file.get(self._axis_datasets[spec]))
                            else:
                                assert_allclose(np.array(obj),np.array(f.file.get(self._axis_datasets[spec])))
                        elif spec in self._data_datasets:  # Check for Data data
                            if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                                self.assertEqual(obj, f.file.get(f._met2gr[par]).get(self._data_datasets[spec]))
                            else:
                                if par == "bunch_length":
                                    if self._blfunc is None:
                                        data = np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec]))
                                    elif self._blfunc == "sqrt":
                                        data = np.sqrt(np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec])))
                                    elif self._blfunc == "calc_bl":
                                        data = Lisa.data.utils.calc_bl(np.array(f.file.get(self._axis_datasets[s.XAXIS])), 
                                                np.array(f.file.get(f._met2gr["bunch_profile"]).get(self._data_datasets[spec])))
                                else:
                                    data = np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec]))
                                assert_allclose(np.array(obj), data)
                        else:
                            raise Exception("Error")

    def test_data_version_15(self):
        f = Lisa.File(op.join(self.file_dir_path, "v15-1.h5"))
        self.specs["source_map"] = [s.XAXIS, s.EAXIS, s.XDATA, s.YDATA]
        self._blfunc = "calc_bl"
        self.do_test(f)

    def test_parameters_version_15(self):
        f = Lisa.File(op.join(self.file_dir_path, "v15-1.h5"))
        self.assertEqual(f.parameters("BunchCurrent"), 0.003)

    def test_data_version_14(self):
        f = Lisa.File(op.join(self.file_dir_path, "v14-1.h5"))
        self.specs["source_map"] = [s.XAXIS, s.EAXIS, s.XDATA, s.YDATA]
        self._blfunc = "calc_bl"
        self.do_test(f)

    def test_parameters_version_14(self):
        f = Lisa.File(op.join(self.file_dir_path, "v14-1.h5"))
        self.assertEqual(f.parameters("BunchCurrent"), 5.0E-4)

    def test_data_version_13(self):
        f = Lisa.File(op.join(self.file_dir_path, "v13-2.h5"))
        self._blfunc = "sqrt"
        self.do_test(f)
        with self.subTest(msg="Raises", what="source_map"):
            with self.assertRaises(DataNotInFile):
                getattr(f, "source_map")

    def test_parameters_version_13(self):
        f = Lisa.File(op.join(self.file_dir_path, "v13-2.h5"))
        self.assertEqual(f.parameters("BunchCurrent"), 1.0E-4)

    def test_data_version_9(self):
        f = Lisa.File(op.join(self.file_dir_path, "v9-1.h5"))
        del self.specs["bunch_population"]
        del self.specs["energy_profile"]
        del self.specs["particles"]
        for par in self.specs:
            with self.subTest(msg=par):
                obj = getattr(f, par)()
                self.assertIsInstance(obj, Lisa.data.DataContainer)
                self.assertEqual(len(obj), len(self.specs[par]))
                for idx, spec in enumerate(self.specs[par]):  # test order in DataContainer
                    with self.subTest(msg=par, spec=spec):
                        self.assertListEqual(np.array(getattr(obj, spec)).tolist(), np.array(obj[idx]).tolist())
                for spec in self.specs[par]:  # test for axis and data
                    if spec == "datagroup":  # skip because only in impedance and REAL and IMAG get tested individually anyway
                        continue 
                    with self.subTest(msg=par, spec_type=spec):
                        obj = getattr(f, par)(spec)
                        if spec in self._axis_datasets:  # Check for Axis data
                            if spec == s.TIME:
                                assert_allclose(np.array(obj),
                                                   np.array(f.file.get(self._axis_datasets[spec]))[1:])
                            else:
                                assert_allclose(np.array(obj),
                                                   np.array(f.file.get(self._axis_datasets[spec]))[0])

                        elif spec in self._data_datasets:  # Check for Data data
                            if s.TIME in self.specs[par]:
                                if par == "bunch_length":
                                    blfunc = np.sqrt
                                else:
                                    blfunc = lambda x: x
                                assert_allclose(np.array(obj), 
                                        blfunc(np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec]))[1:]))
                            else:
                                assert_allclose(np.array(obj), np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec])))
                        else:
                            raise Exception("Error")

        with self.subTest(msg="Raises", what="source_map"):
            with self.assertRaises(DataNotInFile):
                getattr(f, "source_map")

    def test_parameters_version_9(self):
        f = Lisa.File(op.join(self.file_dir_path, "v9-1.h5"))
        self.assertEqual(f.parameters("BunchCurrent"), 9.0E-4)

