#!/usr/bin/env python
#
# Get  Data from the TART telescope archive in the cloud (Made by Max Scheel)
#
# Copyright (c) Tim Molteno 2023.
# ~/.tartvenv/bin/pip3 install minio tqdm
#
import os
import argparse
import datetime
import pytz

from tqdm import tqdm
from minio import Minio

from tart.util import utc

MINIO_API_HOST = "s3.max.ac.nz"
BUCKET_NAME = "tart-hdf"


def main():
    parser = argparse.ArgumentParser(description='Get data from the TART s3 bucket',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dir', required=False, default=".", help="Output directory")

    parser.add_argument('--name', required=False, default=None, help="Output file name prefix - eg 'out_' would produce files 'out_1.hdf', out_2.hdf ...")

    parser.add_argument('--target', required=False,
                        default='signal', help="Telescope name in s3 bucket.")

    parser.add_argument('--catalog', required=False,
                        default='https://tart.elec.ac.nz/catalog', help="Catalog API URL.")

    parser.add_argument('--n', required=False, type=int,
                        default=-1, help="Number of HDF vis files. (-1 means all)")

    parser.add_argument('--start', required=False, default="-60", help="Start time (negative means offset from now).")
    parser.add_argument('--duration', required=False,  default="0", help="Number of minutes to sample for")


    ARGS = parser.parse_args()

    output = ARGS.dir
    if not os.path.exists(output):
        os.mkdir(output)


    # for o in objects:
    #     print(vars(o))
    #     print(dir(o))
    #     break


    start = ARGS.start
    duration_str = ARGS.duration
    duration = float(duration_str)
    duration_dt = datetime.timedelta(days = 0, hours=0, \
                        minutes=duration, seconds=0)

    if start[0] == '-':
        start_offset = float(start[1:])
        utc_now = utc.now()
        delta_t = datetime.timedelta(days = 0, hours=0, \
                        minutes=start_offset, seconds=0)

        start_datetime = utc_now  - delta_t
    else:
        start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)


    stop_datetime = start_datetime + duration_dt
    # Do some logic to avoid boundaries and get the prefix as long as possible
    # This saves us from downloading the entire year's worth of objects just to
    # get some within the same day...
    prefix = f"{ARGS.target}/vis"
    if stop_datetime.year == start_datetime.year:
        prefix += f"/{start_datetime.year}"
    if stop_datetime.month == start_datetime.month:
        prefix += f"/{start_datetime.month}"
    if stop_datetime.day == start_datetime.day:
        prefix += f"/{start_datetime.day}"

    print(f"Getting data from path {prefix}")

    client = Minio(MINIO_API_HOST, secure=True)
    objects = client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True, include_user_meta=True)



    desired_objects = []
    for o in objects:
        if (o.last_modified >= start_datetime) and (o.last_modified <= stop_datetime):
            desired_objects.append(o)

    N = ARGS.n
    if N > 0:
        steps = max(len(desired_objects) // N, 1)
        data_to_get = list(desired_objects)[::steps]
    else:
        data_to_get = list(desired_objects)

    n = len(data_to_get)
    index = 0
    for item in tqdm(data_to_get):

        dirname, fname = os.path.split(item.object_name)
        fname = f"obs_{index:05d}.hdf"
        fname_out = os.path.join(output, fname)
        index = index+1
        client.fget_object(BUCKET_NAME, item.object_name, fname_out)
        # print(fname_out)
