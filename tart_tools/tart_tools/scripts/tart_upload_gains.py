#!/usr/bin/env python
#    Upload gains from local file to api.
#    Max Scheel 2017 - max@max.ac.nz
#    Tim Molteno 2017-2021.

import argparse
import json

from tart_tools.api_handler import AuthorizedAPIhandler, upload_gain

def main():
    parser = argparse.ArgumentParser(
        description="Upload gains from local file to api",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    parser.add_argument("--pw", default="password", type=str, help="API password")
    parser.add_argument("--gains", type=str, required=True, help="local file to upload")

    ARGS = parser.parse_args()

    with open(ARGS.gains, "r") as f:
        data = f.read()
    gains_dict = json.loads(data)

    api_dict = {}
    api_dict['gain'] = gains_dict['gain']
    api_dict['phase_offset'] = gains_dict['phase_offset']
    api = AuthorizedAPIhandler(ARGS.api, ARGS.pw)
    resp = upload_gain(api, api_dict)
    print("SUCCESS")
