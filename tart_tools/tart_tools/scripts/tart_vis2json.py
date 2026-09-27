#!/usr/bin/env python
#
# Generate corresponding visibility (json) files from TART visibility data files.
#
# The main input format is HDF5, as downloaded from the telescope API with
# tart_download_data --vis (and written by tart.imaging.visibility.to_hdf5).
# The deprecated pickle formats ('.pkl', '.vis') are also supported.
#
# Max Scheel 2017 tim@elec.ac.nz
#

import argparse
import json
import os

from tart.imaging import visibility
from tart.util import utc

HDF5_EXTENSIONS = (".hdf", ".hdf5", ".h5")
PICKLE_EXTENSIONS = (".pkl", ".vis")


def _to_plain_list(values):
    """Return a plain python list (numpy arrays are converted elementwise)."""
    if hasattr(values, "tolist"):
        return values.tolist()
    return list(values)


def _visibility_objects(vis):
    """Return a list of visibility.Visibility objects from loaded visibility data.

    Accepts a single Visibility object, a list of Visibility objects (as
    returned by visibility.list_load for pickle files), or the dictionary
    returned by visibility.from_hdf5 (as returned by visibility.list_load for
    HDF5 files). A clear TypeError is raised for anything else.
    """
    if isinstance(vis, visibility.Visibility):
        return [vis]
    if isinstance(vis, dict):
        if "vis_list" not in vis:
            raise TypeError(
                "Unsupported visibility data dictionary (keys: "
                f"{sorted(vis.keys())}): expected the dictionary returned by "
                "tart.imaging.visibility.from_hdf5 with a 'vis_list' key."
            )
        return _visibility_objects(vis["vis_list"])
    if isinstance(vis, (list, tuple)):
        vis_objs = []
        for idx, item in enumerate(vis):
            if not isinstance(item, visibility.Visibility):
                raise TypeError(
                    f"Unsupported visibility data element of type "
                    f"'{type(item).__name__}' at position {idx}: expected a "
                    "tart.imaging.visibility.Visibility object."
                )
            vis_objs.append(item)
        return vis_objs
    raise TypeError(
        f"Unsupported visibility data of type '{type(vis).__name__}': expected "
        "a tart.imaging.visibility.Visibility object, a list of them, or the "
        "dictionary returned by tart.imaging.visibility.from_hdf5."
    )


def create_direct_vis_dict(vis):
    """This function is provided with a visibility object (or a list of
    visibility objects, or the dictionary returned by
    tart.imaging.visibility.from_hdf5). It returns a list of dictionaries
    identical to the json response (one per observation)."""
    vis_dicts = []
    for visobj in _visibility_objects(vis):
        vis_list = []
        timestamp = utc.to_string(visobj.timestamp)
        for b, v in zip(visobj.baselines, visobj.v):
            i, j = b
            # Convert numpy scalars (e.g. complex64 loaded from HDF5) to plain
            # python types so that the result can be serialized with json.dump.
            vis_el = {"i": int(i), "j": int(j),
                      "re": float(v.real), "im": float(v.imag)}
            vis_list.append(vis_el)
        vis_dicts.append({"data": [({"data": vis_list, "timestamp": timestamp},
                                    [])],
                          "timestamp": timestamp})
    return vis_dicts


def load_visibilities(source):
    """Load visibility data from a data file, or normalize already-loaded data.

    'source' can be the path of a supported visibility data file (HDF5:
    '.hdf', '.hdf5', '.h5'; deprecated pickle: '.pkl', '.vis'), or data that
    has already been loaded: a visibility.Visibility object, a list of them,
    or the dictionary returned by tart.imaging.visibility.from_hdf5.

    Returns a dictionary with the keys 'vis_list', 'config', 'ant_pos',
    'gain' and 'phase_offset' (the layout used by
    tart.imaging.visibility.from_hdf5).
    """
    if isinstance(source, (str, os.PathLike)):
        filename = os.fspath(source)
        if not os.path.isfile(filename):
            raise FileNotFoundError(
                f"Visibility data file '{filename}' does not exist."
            )
        extension = os.path.splitext(filename)[1].lower()
        if extension in HDF5_EXTENSIONS:
            loaded = visibility.from_hdf5(filename)
        elif extension in PICKLE_EXTENSIONS:
            loaded = visibility.list_load(filename)
        elif extension == ".json":
            raise ValueError(
                f"Cannot read '{filename}': JSON is an output format of this "
                "tool (and of the telescope imaging API), not a visibility "
                "data format. Supported input formats are HDF5 ('.hdf', "
                "'.hdf5', '.h5') as downloaded with 'tart_download_data "
                "--vis', and deprecated pickle files ('.pkl', '.vis')."
            )
        else:
            raise ValueError(
                f"Unsupported visibility data file '{filename}': extension "
                f"'{extension}' is not supported. Supported input formats are "
                "HDF5 ('.hdf', '.hdf5', '.h5') as downloaded with "
                "'tart_download_data --vis', and deprecated pickle files "
                "('.pkl', '.vis')."
            )
        origin = f"'{filename}'"
    else:
        loaded = source
        origin = "the supplied visibility data"

    vis_objs = _visibility_objects(loaded)
    if not vis_objs:
        raise ValueError(f"No visibilities found in {origin}.")

    if isinstance(loaded, dict):
        config = loaded.get("config")
        ant_pos = loaded.get("ant_pos")
        gain = loaded.get("gain")
        phase_offset = loaded.get("phase_offset")
    else:
        config = None
        ant_pos = None
        gain = None
        phase_offset = None

    if config is None:
        config = vis_objs[0].config
    if ant_pos is None:
        ant_pos = config.get_antenna_positions()
    if ant_pos is None:
        raise ValueError(
            f"{origin} does not contain antenna position information. "
            "Use an HDF5 visibility file (as downloaded with "
            "'tart_download_data --vis') which stores the antenna positions, "
            "gains and phase offsets alongside the visibilities."
        )
    num_antenna = len(ant_pos)
    if gain is None:
        # Deprecated pickle files carry no calibration data. Use neutral
        # gains so that the output JSON remains usable.
        gain = [1.0] * num_antenna
    if phase_offset is None:
        phase_offset = [0.0] * num_antenna

    return {"vis_list": vis_objs, "config": config, "ant_pos": ant_pos,
            "gain": gain, "phase_offset": phase_offset}


def main():
    PARSER = argparse.ArgumentParser(
        description="Generate offline json files from a list of visibility objects files."
    )
    PARSER.add_argument(
        "--vis", required=True, nargs="+",
        help="Visibilities data file(s): HDF5 ('.hdf', '.hdf5', '.h5') as "
             "downloaded with 'tart_download_data --vis', or deprecated "
             "pickle files ('.pkl', '.vis').",
    )
    ARGS = PARSER.parse_args()
    for vis_file in ARGS.vis:
        vis = load_visibilities(vis_file)
        info = json.loads(vis["config"].to_json())
        missing = [k for k in ("frequency", "lat", "lon", "alt")
                   if k not in info]
        if missing:
            raise ValueError(
                f"'{vis_file}': telescope configuration is missing the "
                f"required field(s) {missing}."
            )
        dico_info = {"info": info}
        dico_info["info"]['operating_frequency'] = dico_info["info"]['frequency']
        dico_info["info"]['location'] = {"lat": dico_info["info"]["lat"],
                                         "lon": dico_info["info"]["lon"],
                                         "alt": dico_info["info"]["alt"]}
        ant_pos = _to_plain_list(vis["ant_pos"])
        gains = {"gain": _to_plain_list(vis["gain"]),
                 "phase_offset": _to_plain_list(vis["phase_offset"])}
        vis_dicts = create_direct_vis_dict(vis)
        for vis_dict in vis_dicts:
            vis_dict["info"] = dico_info
            vis_dict["ant_pos"] = ant_pos
            vis_dict["gains"] = gains
            fname = "vis_" + vis_dict["timestamp"].replace(":", "-") + ".json"
            with open(fname, "w") as fp:
                json.dump(vis_dict, fp)
            print(f"Wrote {fname}")


if __name__ == "__main__":
    main()
