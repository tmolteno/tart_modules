#!/usr/bin/env python
#    Save gains from api to local file.
#    Max Scheel 2017 - max@max.ac.nz
#    Tim Molteno 2017 - tim@elec.ac.nz

import argparse
import json

from tart_tools.api_handler import APIhandler, download_current_gain

def main():
    parser = argparse.ArgumentParser(
        description="Save gains from api to local file",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    parser.add_argument(
        "--file", default="gains.json", type=str, help="local file to dump gains"
    )

    ARGS = parser.parse_args()

    api = APIhandler(ARGS.api)

    gains = download_current_gain(api)

    with open(ARGS.file, "w") as outfile:
        json.dump(gains, outfile, sort_keys=True, indent=4, ensure_ascii=False)
