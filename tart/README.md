# TART: Radio-telescope operating software

This module is used for the operation and imaging from the open-source Transient Array Radio Telescope (TART).

For more information see the [TART Github repository](https://github.com/tmolteno/tart_modules), and (https://tart.elec.ac.nz)

## Authors

* Tim Molteno (tim@elec.ac.nz)
* Max Scheel (max@max.ac.nz)

## Installation

Default installation (includes all features):
```
pip install tart
```

For minimal installation (without scipy simulation features):
```
pip install tart[minimal]
```

For installation with plotting support:
```
pip install tart[plotting]
```

For complete installation (all optional features including networking and performance enhancements):
```
pip install tart[all]
```

**Note:** The `[all]` option includes jsonrpclib, matplotlib, pyfftw, requests, and scipy for complete functionality. Some simulation features require scipy and plotting features require matplotlib. These are optional dependencies that will provide helpful error messages if missing. The spectrum analysis feature now works in minimal installations using numpy.fft instead of scipy.fft.

## Development work

If you are developing this package, this should be installed using
```
	make develop
```
in which case changes to the source-code will be immediately available to projects using it.


## NEWS

Changelog:

* 1.4.0   Add a to_json method to visibilty.
* 1.3.5   Fix bugs in x,y array indices.
* 1.3.4   Add routines for converting l,m to x,y and use them.
* 1.3.3   Keep in sync with tart_tools.
* 1.3.1   Added minimal dependency option excluding scipy. Spectrum analysis now uses numpy.fft for better minimal compatibility.
* 1.3.0   Huge refactor to get tests going again.
* 1.2.0b4 Fix up the loading of config data.
* 1.2.0b1 TART tools update (new tart_get_archive_data super-handy tool)
* 1.1.2b8 TART tools update
* 1.1.2b7 Handle expiration of JWT tokens better (in tart_tools)
* 1.1.2b6 Pass the lat and lon to catalog_url
* 1.1.2b5 Require the python-dateutil library
* 1.1.2b4 Require the requests library
* 1.1.2b3 Change API of catalog_url to use lon and lat explicitly
* 1.1.2b0 make h5 to json compatible with tart2ms json import.
* 1.1.1b1 Make sure all get_all_uvw() return meters rather than wavelengths.
* 1.1.0b9 Switch to new based utc class,
		  Fix up some old tests
* 1.1.0b8 Move to separate repository.
		  Better tests.
* 1.1.0b7 Better dealing with h5 files, returning a dict with sufficient information to generate calibrated visibilities.
* 1.1.0b6 Save calibration gains and phases.
* 1.1.0b5 Use raw docstrings for those that contain escape sequences.
* 1.1.0b4 Fix hdf5 visibility output.
* 1.1.0b3 Rework empirical antenna model.
* 1.1.0b0 Add hdf5 IO
* 0.15.5  Added EPHEMERIS_SERVER_HOST, POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD environment variable.
