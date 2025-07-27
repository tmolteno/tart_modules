#!/usr/bin/env python
#    Upload gains from local file to api.
#    Max Scheel 2017 - max@max.ac.nz
#    Tim Molteno 2017-2021.

import argparse
import json
import logging
import numpy as np


from tart_tools import api_handler

logger = logging.getLogger()


def test_gains(config, ARGS):

    new_gain = np.random.uniform(size=config.get_num_antenna())
    new_phase = np.random.uniform(size=config.get_num_antenna())
    api_dict = {}
    api_dict['gain'] = new_gain.tolist()
    api_dict['phase_offset'] = new_phase.tolist()
    api = api_handler.AuthorizedAPIhandler(ARGS.api, ARGS.pw)
    resp = api_handler.upload_gain(api, api_dict)

    gains = api_handler.download_current_gain(api)

    recovered_gain = np.array(gains['gain'])
    recovered_phase = np.array(gains['phase_offset'])

    test_gsum = np.sum(recovered_gain - new_gain)
    if test_gsum != 0:
        print(f"FAIL sum of differences = {test_gsum}")
        print(f"uploaded:  {new_gain}")
        print(f"recovered: {recovered_gain}")
        return

    test_gsum = np.sum(recovered_phase - new_phase)
    if test_gsum != 0:
        print(f"PHASE FAIL sum of differences = {test_gsum}")
        print(f"uploaded:  {new_phase}")
        print(f"recovered: {recovered_phase}")
        return

    print("SUCCESS: gains")


def test_antpos(config, ARGS):

    new_ant_pos = np.random.uniform(size=(config.get_num_antenna(),3))

    api_dict = {}
    api_dict['antenna_positions'] = new_ant_pos.tolist()

    api = api_handler.AuthorizedAPIhandler(ARGS.api, ARGS.pw)

    resp = api.post_payload_with_token(
        "calibration/antenna_positions", api_dict['antenna_positions'])

    ant_pos = api.get("imaging/antenna_positions")
    print("Recovered Antenna Positions")
    print(ant_pos)

    recovered_ant_pos = np.array(ant_pos)

    test_gsum = np.sum(recovered_ant_pos - new_ant_pos)
    if test_gsum != 0:
        print(f"FAIL sum of differences = {test_gsum}")
        print(f"uploaded:  {new_ant_pos}")
        print(f"recovered: {recovered_ant_pos}")
    else:
        print("SUCCESS: antpos")


def main():
    parser = argparse.ArgumentParser(
        description="Test a telescope API by setting stuff and checking it",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://api.elec.ac.nz/tart/mu-udm",
        help="Telescope API server URL."
    )
    parser.add_argument("--pw", default="password",
                        type=str, help="API password")

    logger.setLevel(logging.DEBUG)

    ARGS = parser.parse_args()

    api = api_handler.APIhandler(ARGS.api)
    config = api_handler.get_config(api)

    test_gains(config, ARGS)
    test_antpos(config, ARGS)

