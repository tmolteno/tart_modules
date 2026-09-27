"""
Test the tart_vis2json script.

Regression tests for tart-telescope/notebooks#4 ("Converting HDF5 data to JSON
fails"): HDF5 visibility files (as downloaded with tart_download_data --vis)
must convert to JSON, and unsupported input must give a clear error.
"""
#
# Copyright (c) Tim Molteno 2025. tim@elec.ac.nz
#

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

from tart.imaging import visibility
from tart.operation import settings
from tart.util import utc

from tart_tools.scripts import tart_vis2json

NUM_ANTENNA = 4
NUM_OBS = 2


def make_config():
    config_dict = {
        "name": "Test Telescope",
        "frequency": 1.57542e9,
        "L0_frequency": 1.571328e9,
        "baseband_frequency": 4.092e6,
        "sampling_frequency": 16.368e6,
        "bandwidth": 2.5e6,
        "lat": -45.85177,
        "lon": 170.5456,
        "alt": 270.0,
        "num_antenna": NUM_ANTENNA,
        "orientation": 0.0,
        "axes": ["East", "North", "Up"],
    }
    return settings.from_dict(config_dict)


def make_ant_pos():
    return [[1.0 * i, 0.5 * i, 0.0] for i in range(NUM_ANTENNA)]


def make_vis_list():
    """A list of Visibility objects with values that are exactly
    representable as complex64 (so HDF5 round trips are exact)."""
    baselines = []
    vis_values = []
    for j in range(NUM_ANTENNA):
        for i in range(j + 1, NUM_ANTENNA):
            baselines.append([j, i])
            vis_values.append(complex((i + j) / 8.0, (i - j) / 8.0))
    vis_list = []
    for k in range(NUM_OBS):
        config = make_config()
        config.set_antenna_positions(make_ant_pos())
        vis = visibility.Visibility.from_config(
            config=config,
            timestamp=utc.utc_datetime(2023, 1, 15, 5, 16, 5 + k),
        )
        vis.set_visibilities(v=np.array(vis_values, dtype=np.complex64),
                             b=list(baselines))
        vis_list.append(vis)
    return vis_list, baselines, vis_values


class TestVis2Json(unittest.TestCase):

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.workdir.name)
        self.vis_list, self.baselines, self.vis_values = make_vis_list()
        self.ant_pos = make_ant_pos()
        self.cal_gain = [1.0 + 0.125 * i for i in range(NUM_ANTENNA)]
        self.cal_ph = [0.25 * i for i in range(NUM_ANTENNA)]

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.workdir.cleanup()

    def write_hdf5(self, fname):
        visibility.to_hdf5(self.vis_list, ant_pos=self.ant_pos,
                           cal_gain=self.cal_gain, cal_ph=self.cal_ph,
                           filename=fname)
        return fname

    def run_main(self, *vis_files):
        argv = ["tart_vis2json", "--vis"] + list(vis_files)
        with mock.patch.object(sys, "argv", argv):
            tart_vis2json.main()

    def check_json_files(self, num_files, gain=None, phase_offset=None):
        """Check the JSON output files against the input visibility data."""
        if gain is None:
            gain = self.cal_gain
        if phase_offset is None:
            phase_offset = self.cal_ph
        fnames = sorted(f for f in os.listdir(".") if f.endswith(".json"))
        self.assertEqual(len(fnames), num_files)
        seen = []
        for fname in fnames:
            with open(fname) as fp:
                vis_dict = json.load(fp)
            # Keys needed by consumers such as tart2ms ms_from_json.
            self.assertIn("info", vis_dict)
            self.assertIn("ant_pos", vis_dict)
            self.assertIn("gains", vis_dict)
            self.assertIn("data", vis_dict)
            self.assertIn("timestamp", vis_dict)
            info = vis_dict["info"]["info"]
            self.assertEqual(info["operating_frequency"], 1.57542e9)
            self.assertEqual(info["location"],
                             {"lat": -45.85177, "lon": 170.5456, "alt": 270.0})
            self.assertEqual(vis_dict["ant_pos"], self.ant_pos)
            self.assertEqual(vis_dict["gains"]["gain"], gain)
            self.assertEqual(vis_dict["gains"]["phase_offset"], phase_offset)
            # Each entry of "data" is a (vis_json, source_json) pair.
            self.assertEqual(len(vis_dict["data"]), 1)
            vis_json, source_json = vis_dict["data"][0]
            self.assertEqual(source_json, [])
            self.assertEqual(vis_json["timestamp"], vis_dict["timestamp"])
            data = vis_json["data"]
            self.assertEqual([d["i"] for d in data],
                             [b[0] for b in self.baselines])
            self.assertEqual([d["j"] for d in data],
                             [b[1] for b in self.baselines])
            for d, v in zip(data, self.vis_values):
                # Values must be plain JSON numbers (not numpy scalars).
                self.assertIs(type(d["re"]), float)
                self.assertIs(type(d["im"]), float)
                self.assertEqual(type(d["i"]), int)
                self.assertEqual(type(d["j"]), int)
                self.assertAlmostEqual(d["re"], v.real, places=6)
                self.assertAlmostEqual(d["im"], v.imag, places=6)
            seen.append(vis_json["timestamp"])
        self.assertEqual(len(set(seen)), num_files)
        return fnames

    def test_hdf5_to_json(self):
        """The notebook workflow: tart_vis2json --vis vis_*.hdf"""
        self.write_hdf5("vis_test.hdf")
        self.run_main("vis_test.hdf")
        self.check_json_files(NUM_OBS)

    def test_hdf5_extension_variants(self):
        """'.hdf5' and '.h5' files hold the same data as '.hdf' files."""
        for fname in ("vis_test.hdf5", "vis_test.h5"):
            with self.subTest(fname=fname):
                self.write_hdf5(fname)
                self.run_main(fname)
                self.check_json_files(NUM_OBS)
                for f in os.listdir("."):
                    if f.endswith(".json"):
                        os.remove(f)

    def test_pkl_to_json(self):
        """Deprecated pickle input still converts (with neutral gains)."""
        visibility.list_save(self.vis_list, ant_pos=self.ant_pos,
                             cal_gain=self.cal_gain, cal_ph=self.cal_ph,
                             filename="vis_test.pkl")
        self.run_main("vis_test.pkl")
        self.check_json_files(NUM_OBS,
                              gain=[1.0] * NUM_ANTENNA,
                              phase_offset=[0.0] * NUM_ANTENNA)

    def test_create_direct_vis_dict_from_objects(self):
        """Already-loaded objects (single, list, from_hdf5 dict) are accepted."""
        single = tart_vis2json.create_direct_vis_dict(self.vis_list[0])
        multi = tart_vis2json.create_direct_vis_dict(self.vis_list)
        self.assertEqual(len(single), 1)
        self.assertEqual(single, multi[:1])
        self.write_hdf5("vis_test.hdf")
        from_dict = tart_vis2json.create_direct_vis_dict(
            visibility.from_hdf5("vis_test.hdf"))
        self.assertEqual(len(from_dict), NUM_OBS)
        # No numpy scalars anywhere (this crashed json.dump before the fix).
        json.dumps(from_dict)

    def test_load_visibilities_from_objects(self):
        self.write_hdf5("vis_test.hdf")
        hdf_data = visibility.from_hdf5("vis_test.hdf")
        for source in (hdf_data, self.vis_list, self.vis_list[0]):
            with self.subTest(source=type(source).__name__):
                data = tart_vis2json.load_visibilities(source)
                self.assertEqual(len(data["vis_list"]),
                                 NUM_OBS if source is not self.vis_list[0] else 1)
                self.assertEqual(tart_vis2json._to_plain_list(data["ant_pos"]),
                                 self.ant_pos)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            tart_vis2json.load_visibilities("does_not_exist.hdf")

    def test_unsupported_json_input(self):
        """JSON is an output format; a clear error must explain this."""
        with open("data.json", "w") as fp:
            fp.write("{}")
        with self.assertRaises(ValueError) as cm:
            tart_vis2json.load_visibilities("data.json")
        self.assertIn("JSON", str(cm.exception))

    def test_unsupported_extension(self):
        with open("data.txt", "w") as fp:
            fp.write("not visibilities")
        with self.assertRaises(ValueError) as cm:
            tart_vis2json.load_visibilities("data.txt")
        self.assertIn("not supported", str(cm.exception))

    def test_unsupported_object(self):
        with self.assertRaises(TypeError):
            tart_vis2json.load_visibilities(42)

    def test_str_objects_rejected(self):
        """Regression for tart-telescope/notebooks#4: iterating the keys of
        the from_hdf5 dictionary used to feed plain strings to
        create_direct_vis_dict, crashing with
        AttributeError: 'str' object has no attribute 'baselines'."""
        with self.assertRaises(TypeError):
            tart_vis2json.create_direct_vis_dict(["vis_list", "config"])
        with self.assertRaises(TypeError):
            tart_vis2json.create_direct_vis_dict({"no_vis_list": []})

    def test_missing_vis_argument(self):
        with self.assertRaises(SystemExit):
            with mock.patch.object(sys, "argv", ["tart_vis2json"]):
                tart_vis2json.main()


if __name__ == "__main__":
    unittest.main()
