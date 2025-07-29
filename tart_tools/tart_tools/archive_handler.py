#!/usr/bin/env python
#
# Get  Data from the TART telescope archive in the cloud (Made by Max Scheel)
#
# Copyright (c) Tim Molteno 2023.
# ~/.tartvenv/bin/pip3 install minio tqdm
#
import os
import datetime

from tqdm import tqdm
from minio import Minio

from tart.util import utc

MINIO_API_HOST = "s3.max.ac.nz"
BUCKET_NAME = "tart-hdf"


def handle_archive_request(target, num_observations, output_dir,
                           start_str, duration_str):
    #
    # Used by the command line utility (tart_get_archive_data), as well as to get calibration data
    #
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    duration = float(duration_str)
    duration_dt = datetime.timedelta(days=0, hours=0,
                                     minutes=duration, seconds=0)

    if start_str[0] == '-':
        start_offset = float(start_str[1:])
        utc_now = utc.now()
        delta_t = datetime.timedelta(days=0, hours=0,
                                     minutes=start_offset, seconds=0)

        start_datetime = utc_now - delta_t
    else:
        start_datetime = utc.from_string(start_str)

    stop_datetime = start_datetime + duration_dt
    print(f"start: {start_datetime}")
    print(f"stop:  {stop_datetime}")

    # Do some logic to avoid boundaries and get the prefix as long as possible
    # This saves us from downloading the entire year's worth of objects just to
    # get some within the same day...
    prefix = f"{target}/vis"
    if stop_datetime.year == start_datetime.year:
        prefix += f"/{start_datetime.year}"
    if stop_datetime.month == start_datetime.month:
        prefix += f"/{start_datetime.month}"
    if stop_datetime.day == start_datetime.day:
        prefix += f"/{start_datetime.day}"

    print(f"Getting data from path {prefix}")

    client = Minio(MINIO_API_HOST, secure=True)
    objects = client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True,
                                  include_user_meta=True)

    desired_objects = []
    for o in objects:
        # print(o.object_name, o.last_modified)
        if (o.last_modified >= start_datetime) and (o.last_modified <= stop_datetime):
            desired_objects.append(o)

    N = num_observations
    if N > 0:
        steps = max(len(desired_objects) // N, 1)
        data_to_get = list(desired_objects)[::steps]
    else:
        data_to_get = list(desired_objects)

    index = 0
    for item in tqdm(data_to_get):
        # print(item.object_name)
        #
        dirname, fname = os.path.split(item.object_name)
        fname = f"obs_{index:05d}.hdf"
        fname_out = os.path.join(output_dir, fname)
        index = index+1
        client.fget_object(BUCKET_NAME, item.object_name, fname_out)
