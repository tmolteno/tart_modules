#!/usr/bin/env python
#
# Change the telescope operating mode using the RESTful the API on a TART radio telescope
# Tim Molteno 2021 tim@elec.ac.nz
#
import argparse

from tart_tools.api_handler import AuthorizedAPIhandler

def main():
    parser = argparse.ArgumentParser(
        description="Change telescope mode",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    parser.add_argument("--pw", default="password", type=str, help="API password")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--raw', action="store_true", help="Set raw data mode.")
    mode_group.add_argument('--vis', action="store_true", help="Set vis mode")
    mode_group.add_argument("--mode", type=str, required=False, default=None, help="New mode (vis/raw)")

    ARGS = parser.parse_args()

    mode = None
    if ARGS.raw:
        mode = "raw"
    if ARGS.vis:
        mode = "vis"

    if ARGS.mode is not None:
        mode = ARGS.mode

    if mode is None:
        raise RuntimeError("Either --mode, --raw or --vis must be specified")

    api = AuthorizedAPIhandler(ARGS.api, ARGS.pw)
    resp = api.post_payload_with_token(f"mode/{mode}", {})
    print(f"New mode: {resp}")
