#!/usr/bin/env python
#
# Generate corresponding visibility (json) files from *.vis files
# Max Scheel 2017 tim@elec.ac.nz
#

import argparse
import json

from tart.imaging import visibility
from tart.util import utc

def create_direct_vis_dict(vis):
    """ This function is provided with a visibility object. It returns a dictionary identical to the json response. """
    vis_dicts = []
    for visobj in vis["vis_list"]:
        vis_list = []
        timestamp = utc.to_string(visobj.timestamp)
        for b, v in zip(visobj.baselines, visobj.v):
            i, j = b
            vis_el = {"i": i, "j": j, "re": v.real, "im": v.imag}
            vis_list.append(vis_el)
        vis_dicts.append({"data": [({"data": vis_list, "timestamp": timestamp},
                                    [])],
                          "timestamp": timestamp})
    return vis_dicts


def main():
    PARSER = argparse.ArgumentParser(
        description="Generate offline json files from a list of visibility objects files."
    )
    PARSER.add_argument(
        "--vis", required=False, nargs="*", default="", help="Visibilities data file."
    )
    ARGS = PARSER.parse_args()
    VIS_LIST = []
    if len(ARGS.vis) != 0:
        for vis_file in ARGS.vis:
            VIS_LIST.append(visibility.list_load(vis_file))

    for vis in VIS_LIST:
        dico_info = {"info": json.loads(vis['config'].to_json())}
        dico_info["info"]['operating_frequency'] = dico_info["info"]['frequency']
        dico_info["info"]['location'] = {"lat": dico_info["info"]["lat"],
                                         "lon": dico_info["info"]["lon"],
                                         "alt": dico_info["info"]["alt"]}
        vis_dicts = create_direct_vis_dict(vis)
        for vis_dict in vis_dicts:
            vis_dict["info"] = dico_info
            vis_dict["ant_pos"] = vis["ant_pos"].tolist()
            vis_dict["gains"] = {"gain": vis["gain"].tolist(),
                                 "phase_offset": vis["phase_offset"].tolist()}
            fname = "vis_" + vis_dict["timestamp"] + ".json"
            with open(fname, "w") as fp:
                json.dump(vis_dict, fp)
