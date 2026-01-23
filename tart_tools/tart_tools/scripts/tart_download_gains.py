#!/usr/bin/env python
#    Save gains from api to local file.
#    Max Scheel 2017 - max@max.ac.nz
#    Tim Molteno 2017 - tim@elec.ac.nz

import argparse
import json

from tart_tools.api_handler import APIhandler, download_current_gain
from tart_tools.common_api import *

def main():
    parser = argparse.ArgumentParser(
        description="Save gains from api to local file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    api_parameter(parser)

    parser.add_argument(
        "--file", default="gains.json", type=str, help="local file to dump gains"
    )

    ARGS = parser.parse_args()

    api = APIhandler(ARGS.api)

    gains = download_current_gain(api)

    with open(ARGS.file, "w") as outfile:
        json.dump(gains, outfile, sort_keys=True, indent=4, ensure_ascii=False)
