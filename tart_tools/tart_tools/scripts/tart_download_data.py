#!/usr/bin/env python
#    Download Raw Data from a TART telescope
#    The telescope should be in RAW mode if you want it to capture raw data every minute.
#
# Copyright (c) Tim Molteno 2017-2024.

import argparse
import logging
import os
import urllib.request
import urllib.error
import urllib.parse
import time

from tart_tools.api_handler import APIhandler, download_file, sha256_checksum

logger = logging.getLogger()


def main():
    parser = argparse.ArgumentParser(
        description="Download data from the telescope",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    parser.add_argument(
        "--pw", default="password", required=False, type=str, help="API password"
    )
    parser.add_argument(
        "--dir", type=str, default=".", help="local directory to download"
    )
    parser.add_argument(
        "--n", type=int, default=-1, help="Stop after downloading this many files."
    )
    parser.add_argument(
        "--raw", action="store_true", help="Download Raw Data in HDF format"
    )
    parser.add_argument(
        "--vis", action="store_true", help="Download Visibility Data in HDF format"
    )
    parser.add_argument(
        "--file", type=str, default=None, help="Set the name of the output file"
    )

    ARGS = parser.parse_args()

    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    #api = AuthorizedAPIhandler(ARGS.api, ARGS.pw)
    api = APIhandler(ARGS.api)

    logger.info(f"Downloading Data from {ARGS.api}")
    os.makedirs(ARGS.dir, exist_ok=True)

    tart_endpoint = ARGS.api + "/"

    if not (ARGS.raw or ARGS.vis):
        raise RuntimeError("Either --raw or --vis must be specified")

    if (ARGS.n > 1) and (ARGS.file is not None):
        raise RuntimeError("Cannot specify both --n > 1 and --file")

    while True:
        resp_vis = []
        resp_raw = []
        if ARGS.vis:
            resp_vis = api.get("vis/data")
        if ARGS.raw:
            resp_raw = api.get("raw/data")

        try:
            for entry in (resp_raw + resp_vis)[0:ARGS.n]:
                if "filename" in entry:

                    data_url = urllib.parse.urljoin(tart_endpoint, entry["filename"])

                    file_name = data_url.split("/")[-1]
                    if ((ARGS.n == 1) and (ARGS.file is not None)):
                        file_name = ARGS.file

                    file_path = os.path.join(ARGS.dir, file_name)

                    if os.path.isfile(file_path):
                        if sha256_checksum(file_path) == entry["checksum"]:
                            logger.info("Skipping {}".format(file_path))
                        else:
                            logger.info("Corrupted File: {}".format(file_path))
                            os.remove(file_path)
                            download_file(data_url, entry["checksum"], file_path)
                    else:
                        download_file(data_url, entry["checksum"], file_path)

        except Exception as e:
            logger.exception(e)
        finally:
            if ARGS.n > 0:
                break
            logger.info("Pausing.")
            time.sleep(2)
