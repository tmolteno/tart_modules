#!/usr/bin/env python
#    Upload antenna positions from local file to remote telescope
# Copyright (c) Tim Molteno 2017-2021.

import argparse
import json

import numpy as np



from tart.operation import settings
from tart_tools.api_handler import AuthorizedAPIhandler

def main():
    parser = argparse.ArgumentParser(
        description="Upload antenna positions from local file to remote telescope",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    parser.add_argument("--pw", default="password", type=str, help="API password")
    parser.add_argument("--file", type=str, required=True, help="JSON file  of 'antenna_positions' to upload")
    parser.add_argument("--rotate", type=float, default=0.0, help="Rotate the antenna positions (degrees)")

    ARGS = parser.parse_args()

    with open(ARGS.file, "r") as f:
        data = f.read()
    positions_dict = json.loads(data)

    if "antenna_positions" in positions_dict:
        api_dict = {}
        api_dict['antenna_positions'] = positions_dict['antenna_positions']

        if (ARGS.rotate != 0.0):
            original_positions = api_dict['antenna_positions']

            print(f"Rotating positions by {ARGS.rotate} degrees")
            rot_rad = np.radians(ARGS.rotate)

            new_positions = settings.rotate_location(
                np.degrees(rot_rad), np.array(original_positions).T
            )
            pos_list = (np.array(new_positions).T).tolist()
            api_dict["antenna_positions"] = pos_list

        api = AuthorizedAPIhandler(ARGS.api, ARGS.pw)
        print(f"Uploading {api_dict}")
        resp = api.post_payload_with_token(
            "calibration/antenna_positions", api_dict["antenna_positions"])
        print(f"SUCCESS {resp}")
    else:
        raise Exception("JSON file should have an element called 'antenna_positions'")
