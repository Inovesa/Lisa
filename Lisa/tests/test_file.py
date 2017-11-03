from unittest_helpers import CustomTestCase
import numpy as np
import h5py
# rethink importing it
import Lisa



s = Lisa.Axis

import time
import os.path as op


class FileTest(CustomTestCase):
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

    def do_test(self, file):
        f = file
        for par in self.specs:
            with self.subTest(msg=par):
                obj = getattr(f, par)()
                self.assertIsInstance(obj, Lisa.core.file.DataContainer)
                self.assertEqual(len(obj), len(self.specs[par]))
                for idx, spec in enumerate(self.specs[par]):
                    with self.subTest(msg=par, spec=spec):
                        # this tests if the correct order is used in DataContainer
                        # To be compatible with multiple inovesa versions we convert this explicitly to a np.array
                        if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                            self.assertEqual(getattr(obj, spec), obj[idx])
                        else:
                            self.assertListEqual(np.array(getattr(obj, spec)).tolist(), np.array(obj[idx]).tolist())
                for spec in self.specs[par]:
                    with self.subTest(msg=par, spec_type=spec):
                        obj = getattr(f, par)(spec)
                        if spec in self._axis_datasets:
                            if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                                self.assertEqual(obj, f.file.get(self._axis_datasets[spec]))
                            else:
                                self.assertListEqual(np.array(obj).tolist(), np.array(f.file.get(self._axis_datasets[spec])).tolist())
                        elif spec in self._data_datasets:
                            if isinstance(obj, h5py.Dataset):  # if it is a h5py dataset we can compare them directly
                                self.assertEqual(obj, f.file.get(f._met2gr[par]).get(self._data_datasets[spec]))
                            else:
                                self.assertListEqual(np.array(obj).tolist(), np.array(f.file.get(f._met2gr[par]).get(self._data_datasets[spec])).tolist())
                        else:
                            raise Exception("Error")

    def test_version_15(self):
        f = Lisa.File(op.join(self.file_dir_path, "v15-1.h5"))
        self.specs["source_map"] = [s.XAXIS, s.EAXIS, s.XDATA, s.YDATA]
        self.do_test(f)

    def test_version_14(self):
        f = Lisa.File(op.join(self.file_dir_path, "v14-1.h5"))
        self.specs["source_map"] = [s.XAXIS, s.EAXIS, s.XDATA, s.YDATA]
        self.do_test(f)

    def test_version_13(self):
        f = Lisa.File(op.join(self.file_dir_path, "v13-2.h5"))
        self.do_test(f)
        with self.assertRaises(ValueError):
            getattr(f, "source_map")

    def test_version_9(self):
        f = Lisa.File(op.join(self.file_dir_path, "v9-1.h5"))
        del self.specs["bunch_population"]
        del self.specs["energy_profile"]
        del self.specs["particles"]
        self.do_test(f)
        with self.assertRaises(ValueError):
            getattr(f, "source_map")
