# TART: Radio-telescope command line tools

This module provides command line tools for operating Transient Array Radio Telescope (TART). These tools are

* tart_calibrate
* tart_calibration_data
* tart_download_antenna_positions
* tart_upload_antenna_positions
* tart_get_archive_data
* tart_download_data
* tart_download_gains
* tart_image
* tart_upload_gains
* tart_set_mode
* tart_vis2json


To generate an image from a telescope, try the following command which should display the current view from a telescope
on top of Signal-Hill near Dunedin New Zealand.

    tart_image --api https://tart.elec.ac.nz/signal --display

For more information see the [TART website](https://tart.elec.ac.nz)

## Install Instructions

tart_tools is available from standard python package repositories. Try:

    pip3 install tart_tools


## Authors

* Tim Molteno (tim@elec.ac.nz)
* Max Scheel (max@max.ac.nz)

## Development work

If you are developing this package, this should be installed using
```
	make develop
```
in which case changes to the source-code will be immediately available to projects using it.


## NEWS
* 1.4.2 Make download_file download to a temporary file before copying to actual file.
* 1.4.0 Add an archive_handler
* 1.3.0 Huge refactor to get tests going again.
* 1.2.2 Add a backoff factor. So that failed requests are delayed
* 1.2.1 Add retry logic to the requests.get methods.
* 1.2.0b3 Update links to the github repository.
* 1.2.0b2 tart_get_archive_data: Use a five digit leading-zeros number for multiple downloads,
          default to all data if --n is not specified
* 1.2.0b1 new tool: tart_get_archive_data super convenient to query the AWS cloud archive of TART data.
* 1.1.2b8 Add an argument --rotate to tart_upload_antenna_positions (for first stage of calibration)
* 1.1.2b7 Handle expiration of JWT tokens better (in tart_tools)
* 1.1.2b7 TART tools update. Add a command line switch to specify output file for tart_download_data'
* 1.1.2b6 Pass the lat and lon to catalog_url
* 1.1.2b5 Require the python-dateutil library
* 1.1.2b4 Require the requests library
* 1.1.2b3 Change API of catalog_url to use lon and lat explicitly
* 1.1.2b1 Fix a missing checksum call if a local file was partially downloaded (tart_download_data).
* 1.1.2b0 Make h5 to json compatible with tart2ms json import.
* 1.1b.8 New versioning to match tart. Move to new repository

* 0.2.0b14. Improve API handler code.
* 0.2.0b13. Clean up code to use other API endpoints.
            Add CLI to --ignore some antennas
            Add --n option to tart_download_data to stop after n downloads (used to grab the latest raw file)
            Add CLI to use the influxdb
* 0.2.0b12. Fix bug in get-gains option.
* 0.2.0b11. Add a tart_set_mode binary.
* 0.2.0b9. Add a timeout to all HTTP requests.
* 0.2.0b8. Add a put method to the authorized api handler.
* 0.2.0b7. Fix typo in tart_calibrate that stopped calibration working.
* 0.2.0. New tart_download_data function.
* 0.1.5. Python3 compatability changes
