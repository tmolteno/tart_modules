#!/usr/bin/env python
#
# Get  Data from the TART telescope archive in the cloud (Made by Max Scheel)
#
# Copyright (c) Tim Molteno 2023-2025.
# ~/.tartvenv/bin/pip3 install minio tqdm
#
import argparse

from tart_tools.archive_handler import handle_archive_request


def main():
    parser = argparse.ArgumentParser(description='Get data from the TART s3 bucket',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dir', required=False, default=".",
                        help="Output directory")

    parser.add_argument('--name', required=False,
                        default=None,
                        help="Output file name prefix - eg 'out_' would produce files 'out_1.hdf', out_2.hdf ...")

    parser.add_argument('--target', required=False,
                        default='signal', help="Telescope name in s3 bucket.")

    parser.add_argument('--n', required=False, type=int,
                        default=-1, help="Number of HDF vis files. (-1 means all)")

    parser.add_argument('--start', required=False, default="-60",
                        help="Start time (negative means offset from now).")
    parser.add_argument('--duration', required=False,  default="0",
                        help="Number of minutes to sample for")

    ARGS = parser.parse_args()

    handle_archive_request(target=ARGS.target,
                           num_observations=ARGS.n,
                           output_dir=ARGS.dir,
                           start_str=ARGS.start,
                           duration_str=ARGS.duration)
