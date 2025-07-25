#!/usr/bin/env python
#
# Get Calibration Data from the TART telescope
#
# Copyright (c) Tim Molteno 2017-2021.

import argparse
import numpy as np
import time
import json


from tart.operation import settings
from tart.imaging import visibility
from tart.imaging import calibration

from tart_tools import api_handler
from tart_tools import api_imaging
from tart.util import utc


def split_param(x):
    rot_degrees = x[0]
    re = np.concatenate(([1], x[1:24]))
    im = np.concatenate(([0], x[24:47]))
    gains = np.sqrt(re * re + im * im)
    phase_offsets = np.arctan2(im, re)
    return rot_degrees, gains, phase_offsets


def load_data(api, config):
    print("Loading new data from {}...".format(api.root))
    vis_json = api.get("imaging/vis")
    ts = api_imaging.vis_json_timestamp(vis_json)

    cat_url = api.catalog_url(lon=config.get_lon(),
                                lat=config.get_lat(),
                                datestr=utc.to_string(ts))
    print(f"Getting catalog from {cat_url}")
    src_json = api.get_url(cat_url)

    print("Loading Complete")
    return vis_json, src_json


def main():
    PARSER = argparse.ArgumentParser(
        description="Generate Calibration Data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    PARSER.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    PARSER.add_argument(
        "--file",
        required=False,
        default="calibration_data.json",
        help="Calibration Output JSON file.",
    )
    PARSER.add_argument(
        "--n", type=int, default=5, help="Number of samples in the JSON data file."
    )
    PARSER.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval (in minutes) between samples in the JSON data file.",
    )
    PARSER.add_argument(
        "--catalog",
        required=False,
        default="https://tart.elec.ac.nz/catalog",
        help="Catalog API URL.",
    )

    ARGS = PARSER.parse_args()

    api = api_handler.APIhandler(ARGS.api)

    info = api.get("info")
    ant_pos = api.get("imaging/antenna_positions")
    config = settings.from_api_json(info["info"], ant_pos)
    gains_json = api.get("calibration/gain")

    ret = {"info": info, "ant_pos": ant_pos, "gains": gains_json}
    data = []
    for i in range(ARGS.n):
        vis_json, src_json = load_data(api, config)
        data.append([vis_json, src_json])
        if i != ARGS.n - 1:
            print("Sleeping {} minutes".format(ARGS.interval))
            time.sleep(ARGS.interval * 60)
    ret["data"] = data
    with open(ARGS.file, "w") as fp:
        json.dump(ret, fp, indent=4, separators=(",", ": "))
