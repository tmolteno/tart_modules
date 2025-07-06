import unittest

import numpy as np

from tart.imaging import visibility
from tart.operation import settings
from tart.util import angle, skyloc, utc

VIS_DATA_FILE = "tart/test/test_data/fpga_2019-02-22_05_11_41.765212.vis"
ANT_POS_FILE = "tart/test/test_calibrated_antenna_positions.json"


def dummy_vis():
    config = settings.from_file("tart/test/test_telescope_config.json")
    ret = visibility.Visibility.from_config(config=config, timestamp=utc.now())
    b = []
    v = []
    for j in range(24):
        for i in range(24):
            if i > j:
                b.append([j, i])
                v.append(np.random.uniform(0, 1) + np.random.uniform(0, 1) * (1.0j))
    ret.set_visibilities(b=b, v=np.array(v))
    return ret


def dummy_vis_list():
    ret = []
    for i in range(2):
        ret.append(dummy_vis())
    return ret


class TestVisibility(unittest.TestCase):
    def setUp(self):
        self.v_array = dummy_vis_list()
        self.v_array[0].config.load_antenna_positions(
            cal_ant_positions_file=ANT_POS_FILE
        )
        self.ant_pos=self.v_array[0].config.get_antenna_positions()

    def check_vis(self, dut, dut2):
        delta = np.sum(np.abs(np.array(dut.v) - np.array(dut2.v)))
        self.assertTrue(delta <= 1.0e10)
        self.assertTrue((np.array(dut.baselines) == np.array(dut2.baselines)).all())
        self.assertEqual(dut.timestamp, dut2.timestamp)

        keys = dut.config.Dict.keys()
        for k in keys:
            self.assertEqual(dut.config.Dict[k], dut2.config.Dict[k])

    def test_load_save(self):
        dut = dummy_vis()
        visibility.Visibility_Save_JSON(self.v_array[0], "test_vis.json")
        # TODO add tests here

    def test_list_load_save_hdf(self):
        dut_list = dummy_vis_list()
        fname = "test_vis_list_io.hdf"
        visibility.list_save(dut_list, ant_pos=self.ant_pos,
                             cal_gain=[0], cal_ph=[0],
                             filename=fname)  # ant_pos, cal_gain, cal_ph, filename
        dut2_list = visibility.list_load(fname)['vis_list']
        for x, y in zip(dut_list, dut2_list):
            self.check_vis(x, y)


    def test_hdf5(self):
        dut = dummy_vis()
        fname = "test_vis.hdf"
        visibility.to_hdf5([dut],  ant_pos=self.ant_pos,
                           cal_gain=[0], cal_ph=[0],
                           filename=fname)
        dut2 = visibility.from_hdf5(fname)
        print(dut2)
        vl = dut2['vis_list']
        self.check_vis(dut, vl[0])


    def test_zero_rotation(self):
        v = self.v_array[0]
        v_before = np.array(v.v)  # Copy the visibilities
        el1 = v.phase_el
        az1 = v.phase_az

        ra, decl = v.config.get_loc().horizontal_to_equatorial(v.timestamp, el1, az1)

        v.rotate(skyloc.Skyloc(ra, decl))

        v_after = np.array(v.v)
        self.assertEqual(v.phase_el.to_degrees(), el1.to_degrees())

        for x, y in zip(v_before, v_after):
            self.assertAlmostEqual(np.abs(x), np.abs(y), 4)

    def test_full_rotation(self):
        v = self.v_array[0]
        v_before = np.array(v.v)  # Copy the visibilities
        el1 = v.phase_el
        az1 = v.phase_az
        ra, decl = v.config.get_loc().horizontal_to_equatorial(v.timestamp, el1, az1)

        # Pick a baseline

        # Calculate the angle to offset the RA, DEC to produce a full rotation
        #

        v.rotate(skyloc.Skyloc(ra + angle.from_dms(0.05), decl))
        v_after = np.array(v.v)
        self.assertAlmostEqual(v.phase_el.to_degrees(), el1.to_degrees(), 0)
        for x, y in zip(v_before, v_after):
            self.assertAlmostEqual(np.angle(x), np.angle(y), 1)
            self.assertAlmostEqual(np.abs(x), np.abs(y), 2)
