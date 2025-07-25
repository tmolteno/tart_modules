#!/usr/bin/env python
#
# Generate and Image from the RESTful the API on a TART radio telescope
# Copyright (c) Tim Molteno 2017-2022.
#
import matplotlib
import os

if os.name == "posix" and "DISPLAY" not in os.environ:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

import logging
import argparse
import sys
import threading
import datetime
import json

import numpy as np

from tart_tools import api_imaging
from tart_tools import api_handler
from tart.operation import settings
from tart.imaging import elaz
from tart.util import utc

from copy import deepcopy

logger = logging.getLogger()


def handle_image(args, img, n_bin, title, time_repr, source_json=None):
    """ This function manages the output of an image, drawing sources e.t.c."""
    image_title = "{}_{}".format(title, time_repr)
    if args.fits:
        fname = "{}.fits".format(image_title)
        api_imaging.save_fits_image(
            img, fname=fname, out_dir=args.dir, timestamp=time_repr
        )
        print("Generating {}".format(fname))
    if args.PNG or args.display:
        api_imaging.make_image(plt, img, image_title, n_bin, source_json, args.healpix)
    if args.PNG:
        fname = "{}.png".format(image_title)
        plt.savefig(os.path.join(args.dir, fname))
        print("Generating {}".format(fname))
    if args.display:
        plt.show()


def image_stats(img):
    rsky = np.real(img.flatten())

    npix = rsky.shape[0]

    max_p = np.max(rsky)
    sdev_p = np.std(rsky)
    min_p = np.min(rsky)
    mean_p = np.mean(rsky)
    med_p = np.median(rsky)
    deviation = np.abs(med_p - rsky)
    mad_p = np.median(deviation)

    logger.info(
        "'N_s':{}, 'S/N': {}, 'min': {}, 'max': {}, 'mean': {}, 'sdev': {}, 'R_mad': {}, 'MAD': {}, 'median': {}".format(
            npix,
            (max_p / sdev_p),
            min_p,
            max_p,
            mean_p,
            sdev_p,
            (max_p / mad_p),
            mad_p,
            med_p,
        )
    )

    return max_p, min_p, mad_p


def main():
    PARSER = argparse.ArgumentParser(
        description="Generate an image using the web api ofs a TART radio telescope.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    PARSER.add_argument(
        "--api",
        required=False,
        default="https://tart.elec.ac.nz/signal",
        help="Telescope API server URL.",
    )
    PARSER.add_argument(
        "--catalog",
        required=False,
        default="https://tart.elec.ac.nz/catalog",
        help="Catalog API URL.",
    )
    PARSER.add_argument(
        "--file",
        required=False,
        default=None,
        help="Get data from a calibration JSON file.",
    )

    PARSER.add_argument(
        "--gains",
        required=False,
        default=None,
        help="Use a local JSON file containing antenna gains to create the image image.",
    )
    PARSER.add_argument(
        "--vis",
        required=False,
        default=None,
        help="Use a local JSON file containing the visibilities to create the image image.",
    )
    PARSER.add_argument("--dir", required=False, default=".", help="Output directory.")
    PARSER.add_argument(
        "--rotation",
        type=float,
        default=0.0,
        help="Apply rotation (in degrees) to the antenna positions.",
    )
    PARSER.add_argument(
        "--nfft",
        type=int,
        default=10,
        help="Log(2) of the number of points in the fft.",
    )

    PARSER.add_argument(
        "--dirty", action="store_true", help="Create a direct IFFT dirty image."
    )
    PARSER.add_argument(
        "--difmap",
        action="store_true",
        help="Use difmap to generate a CLEAN image (requires extenal difmap executable).",
    )
    PARSER.add_argument(
        "--aipy", action="store_true", help="Use AIPY to generate a CLEAN image."
    )
    PARSER.add_argument(
        "--moresane",
        action="store_true",
        help="Use MORESANE to generate a wavelet based compressed representation (requires extenal difmap executable).",
    )
    PARSER.add_argument("--beam", action="store_true", help="Generate beam image")

    PARSER.add_argument(
        "--healpix",
        action="store_true",
        help="Use HealPIX to map the resulting image onto a projected circle.",
    )

    PARSER.add_argument(
        "--display", action="store_true", help="Display Image to the user"
    )
    PARSER.add_argument(
        "--log", action="store_true", help="Output the log of the image"
    )
    PARSER.add_argument(
        "--fits", action="store_true", help="Generate a FITS format image"
    )
    PARSER.add_argument(
        "--PNG", action="store_true", help="Generate a PNG format image"
    )
    PARSER.add_argument(
        "--show-sources",
        action="store_true",
        help="Show known sources on images (only works on PNG).",
    )

    source_json = None

    ARGS = PARSER.parse_args()

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

    if ARGS.file:
        logger.info("Getting Data from file: {}".format(ARGS.file))
        # Load data from a JSON file
        with open(ARGS.file, "r") as json_file:
            calib_info = json.load(json_file)

        info = calib_info["info"]
        ant_pos = calib_info["ant_pos"]
        config = settings.from_api_json(info["info"], ant_pos)

        flag_list = []  # [4, 5, 14, 22]

        original_positions = deepcopy(config.get_antenna_positions())

        gains_json = calib_info["gains"]
        gains = np.asarray(gains_json["gain"])
        phase_offsets = np.asarray(gains_json["phase_offset"])
        config = settings.from_api_json(info["info"], ant_pos)

        measurements = []
        for d in calib_info["data"]:
            vis_json, source_json = d
            cv, timestamp = api_imaging.vis_calibrated(
                vis_json, config, gains, phase_offsets, flag_list
            )
            src_list = elaz.from_json(source_json, 0.0)

    else:
        logger.info("Getting Data from API: {}".format(ARGS.api))

        api = api_handler.APIhandler(ARGS.api)
        config = api_handler.get_config(api)

        if ARGS.gains is None:
            gains = api.get("calibration/gain")
        else:
            with open(ARGS.gains, "r") as json_file:
                gains = json.load(json_file)

        if ARGS.vis is None:
            vis_json = api.get("imaging/vis")
        else:
            with open(ARGS.vis, "r") as json_file:
                vis_json = json.load(json_file)

        ts = api_imaging.vis_json_timestamp(vis_json)
        if ARGS.show_sources:
            cat_url = api.catalog_url(lon=config.get_lon(),
                                      lat=config.get_lat(),
                                      datestr=utc.to_string(ts))
            source_json = api.get_url(cat_url)

        logger.info("Data Download Complete")

        cv, timestamp = api_imaging.vis_calibrated(
            vis_json, config, gains["gain"], gains["phase_offset"], flag_list=[]
        )

    api_imaging.rotate_vis(
        ARGS.rotation, cv, reference_positions=deepcopy(config.get_antenna_positions())
    )
    n_bin = 2 ** ARGS.nfft

    time_repr = "{:%Y_%m_%d_%H_%M_%S_%Z}".format(timestamp)

    # Image informstion
    # prihdr.set('DATE', timestamp)
    # prihdr.set('DATE-OBS', timestamp)
    #
    # prihdr.set('TIMESYS', 'UTC')
    # prihdr.set('INSTRUME', 'TART')
    # prihdr.set('TELESCOP', 'TART')
    # prihdr.set('OBSERVER' 'CASA simulator')
    # prihdr.set('ORIGIN', 'tart_tools tart.elec.ac.nz ')
    #
    # prihdr.set('OBSRA', 2.889721000000E+02)
    # prihdr.set('OBSDEC', -7.466052777778E+01)
    # prihdr.set('OBSGEO-X', 5.111202828133E+06)
    # prihdr.set('OBSGEO-Y', 2.001309252764E+06)
    # prihdr.set('OBSGEO-Z', -3.237339358474E+06)

    # Processing

    if ARGS.dirty or ARGS.moresane or ARGS.aipy:
        cal_ift, cal_extent, n_fft, bin_width = api_imaging.image_from_calibrated_vis(
            cv, nw=n_bin / 4, num_bin=n_bin
        )

        ## Scale to both abs and MAD
        img = np.abs(cal_ift)
        max_p, min_p, mad_p = image_stats(img)
        ift_scaled = (img - min_p) / mad_p

    if ARGS.beam or ARGS.moresane or ARGS.aipy:
        beam = np.abs(
            api_imaging.beam_from_calibrated_vis(cv, nw=n_bin / 4, num_bin=n_bin)
        )

    if ARGS.difmap:
        fits_bin = 2 ** 12

        fitsfile = "{}.uvfits".format(time_repr)
        uvfitspath = os.path.join(ARGS.dir, fitsfile)
        fits_gen = api_imaging.get_uv_fits(cv)
        fits_gen.write(uvfitspath)

        commands = """
! Basic imaging instructions by Tim Molteno, based around the final_clean script
! by Dan Homan,  dhoman@nrao.edu
debug = False
observe {}
mapsize {}, {}
docont=false
mapcolor color
integer clean_niter;
float clean_gain; clean_gain = 0.03
float dynam;
float flux_peak;

! Define the inner loop as a macro.

float flux_cutoff
float dyn_range
float last_in_rms
float in_rms
float target_rms
float V_rms

#+map_residual \
flux_peak = peak(flux);\
flux_cutoff = imstat(rms) * dynam;\
while(abs(flux_peak)>flux_cutoff);\
 clean clean_niter,clean_gain;\
 flux_cutoff = imstat(rms) * dynam;\
 flux_peak = peak(flux);\
end while

! The following macro stops
! when the the in_frame RMS matches the
! the V RMS OR if there is not improvement
! in the in_frame RMS

#+deep_map_residual \
in_rms = imstat(rms);\
print "Target RMS: ", target_rms, "  In Frame RMS: ", in_rms;\
while(in_rms > target_rms);\
 clean min(200*(in_rms/target_rms),1000),clean_gain;\
 last_in_rms = in_rms;\
 in_rms = imstat(rms);\
 print "Target RMS: ", target_rms, "  In Frame RMS: ", in_rms;\
 if(last_in_rms <= in_rms);\
  in_rms = target_rms;\
 end if;\
 selfcal;\
end while


! select V and get the V_rms for comparison
select v
clrmod true,true,true
delwin
uvw 0,-2
uvtaper 0
V_rms = imstat(rms)

! select the stokes to clean
select i

! clear previous model
clrmod true,true,true

! delete any windows
delwin

! remove any tapering
uvtaper 0

print "*********** FIRST TRY SUPER-UNIFORM WEIGHTING **********"
print "**** -- only if dynamic range is higher than 10 -- *****"

dynam = 10
clean_niter = 50
uvw 20,-1
map_residual
uvw 10,-1
map_residual
clean_niter = 50

print "*********** REGULAR UNIFORM WEIGHTING NEXT ***************"

uvw 2,-1
dynam = 6
map_residual
print "********** DEEP CLEANING AT NATURAL WEIGHTING **************"
uvw 0,-2
! now let clean go deep
target_rms = imstat(noise)/8
if(target_rms < imstat(rms))
  deep_map_residual
else
  ! clean 1 component just to have something to restore
  clean 1, clean_gain
end if

in_rms = imstat(rms)
print "********** FINAL CLEAN IS FINISHED **************"
print "Target RMS was: ", target_rms, " Reached RMS: ", in_rms
print "For comparison uncleaned V RMS is: ", V_rms
print "*************************************************"

device {}_difmap.png/png
mappl cln
!wmap {}_clean.fits
exit
""".format(
            uvfitspath, fits_bin, 1.3 * 648000000.0 / fits_bin, uvfitspath, uvfitspath
        )
        f = open("difmap_cmds", "w")
        f.write(commands)
        f.close()
        os.system("/usr/local/bin/difmap < difmap_cmds")
        # os.system("vips scale {}_clean.fits {}_grey.png".format(uvfitsfile, uvfitsfile))

    if ARGS.moresane:
        from pymoresane.main import DataImage

        degrees_per_pixel = 180.0 / len(beam)

        sane = DataImage(
            img / np.sum(beam),
            beam,
            mask_data=None,
            cdelt1=degrees_per_pixel,
            cdelt2=degrees_per_pixel,
        )
        logger = sane.make_logger("INFO")

        beam_width_degrees = 3.0
        stop_scale = ARGS.nfft - 1  # Maximum size feature (full image width)
        start_scale = int(np.log2(n_bin * beam_width_degrees / 180.0))

        print("Start Scale {}".format(start_scale))
        sane.moresane(
            subregion=None,
            sigma_level=4.0,
            loop_gain=0.05,
            tolerance=0.75,
            accuracy=1e-6,
            major_loop_miter=100,
            minor_loop_miter=50,
            all_on_gpu=False,
            decom_mode="ser",
            core_count=1,
            conv_device="cpu",
            conv_mode="circular",
            extraction_mode="cpu",
            enforce_positivity=True,
            edge_suppression=True,
            edge_offset=int(n_bin / 30),
            flux_threshold=0,
            neg_comp=False,
            edge_excl=0,
            int_excl=0,
        )
        sane.restore()

    if ARGS.aipy:
        import aipy

        clean, info = aipy.deconv.clean(
            img,
            beam,
            gain=0.1,
            maxiter=1000,
            tol=1e-5,
            verbose=True,
            stop_if_div=True,
            pos_def=False,
        )

        if True:
            b_restore = np.fft.fftshift(beam)
        else:
            # b_restore = a.img.gaussian_beam(3, shape=img.shape) #* np.max(beam)
            b_center = len(beam) / 2
            b_width_px = int(3.0 * n_bin / 180)
            b_restore_shifted = np.zeros_like(beam)

            y, x = np.ogrid[-b_center:b_center, -b_center:b_center]
            mask = x * x + y * y <= b_width_px ** 2

            b_restore_shifted[mask] = np.fft.fftshift(beam)[mask]
            b_restore = np.fft.fftshift(b_restore_shifted)

        restored_image = np.abs(
            np.fft.ifft2(np.fft.fft2(clean) * np.fft.fft2(b_restore))
        )  # Cropped PSF Restoration

        print("Clean", info["success"], np.min(restored_image), np.max(restored_image))

    # Do output images

    if ARGS.moresane:
        handle_image(ARGS, sane.restored, n_bin, "MORESANE", time_repr, source_json)

    if ARGS.beam:
        if ARGS.log:
            beam = np.log10(beam)
        handle_image(ARGS, beam, n_bin, "beam", time_repr)

    if ARGS.dirty:
        handle_image(ARGS, ift_scaled, n_bin, "dirty", time_repr, source_json)

    if ARGS.aipy:
        handle_image(ARGS, restored_image, n_bin, "clean", time_repr, source_json)
