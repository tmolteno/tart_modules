#!/usr/bin/env python
#
#    Download Antenna Positions
#    Tim Molteno 2017 - tim@elec.ac.nz

import argparse
import json

from tart_tools.api_handler import APIhandler
from tart_tools.common_api import *

def main():
    parser = argparse.ArgumentParser(
        description="Save antenna positions from api to local file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    api_parameter(parser)
    parser.add_argument(
        "--file",
        default="antenna_positions.json",
        type=str,
        help="local file to dump antenna positions",
    )

    ARGS = parser.parse_args()

    api = APIhandler(ARGS.api)

    pos = api.get("imaging/antenna_positions")

    out_json = {}
    out_json["antenna_positions"] = pos
    with open(ARGS.file, "w") as outfile:
        json.dump(out_json, outfile, sort_keys=True, indent=4, ensure_ascii=False)
