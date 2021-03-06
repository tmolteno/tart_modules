# TART: Radio-telescope operating software
    
This module is used for the operation and imaging from the open-source Transient Array Radio Telescope (TART).

For more information see the [TART Github repository](https://github.com/tmolteno/TART)

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

Changelog:

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
