## Utility functions for imaging
import numpy as np

from tart.imaging import synthesis
from tart.operation import settings

# Following for simulation only
from tart.util import angle
from tart.imaging import antenna_model
from tart.imaging import radio_source
from tart.imaging import location
from tart.simulation import antennas
from tart.simulation import radio
from tart.simulation import skymodel
from tart.imaging import calibration


def deg_to_pix(num_bins, deg):
    pix_per_degree = num_bins / 180.0
    d = deg*pix_per_degree
    return d


def get_lm_index(l, m, image_size):
    ''' The l axis is along the +x in the image plane.
        The numpy array index for this is the second index. For example
        the point [image_size , 0] is in the LOWER LEFT of the image when displayed
        by imshow.

        https://matplotlib.org/stable/users/explain/artists/imshow_extent.html#imshow-extent

         0, 0  -> [image_size // 2, image_size // 2]
        -1, 1  -> [0 , 0]
        -1, -1 -> [image_size-1, 0]
        1, -1  -> [image_size-1, image_size-1]
        1,  1  -> [0, image_size-1]
    '''
    x0 = image_size // 2
    max_index = image_size - 0.5
    index0 = np.floor(x0 - (m*max_index/2))
    index1 = np.floor(x0 + (l*max_index/2))
    return int(index0), int(index1)


def get_baseline_indices(num_ant):
    bl_indices = []
    for i in range(num_ant-1):
        for j in range(i + 1, num_ant):
            bl_indices.append([i, j])
    return bl_indices


def get_baselines(ant_pos):
    num_ant = ant_pos.shape[0]
    bl_indices = get_baseline_indices(num_ant)
    i_indices = bl_indices[:, 0]
    j_indices = bl_indices[:, 1]

    return ant_pos[j_indices, :] - ant_pos[i_indices, :]


def ant_pos_to_uv(ant_pos, i, j):
    return ant_pos[j] - ant_pos[i]


def apply_complex_gains(v_complex, gains_complex, i, j):
    return v_complex * gains_complex[i] * np.conj(gains_complex[j])


def ifft_imaging(uv_plane, module=np.fft):
    return module.fft.fftshift(
        module.fft.ifft2(
            module.fft.ifftshift(uv_plane)
            )
        )


def uv_index(u, v, num_bins, uv_max):
    ''' A little function to produce the index into the u-v array
        for a given value (u, measured in wavelengths)
    '''
    middle = num_bins // 2

    u_pix = middle + (u / uv_max)*(num_bins/2)
    v_pix = middle + (v / uv_max)*(num_bins/2)

    return int(u_pix), int(v_pix)


def grid_visibility(uv_plane, v_complex, baselines):
    num_bins = uv_plane.shape[0]
    uv_max = num_bins / 4   # (1.2 * np.pi)

    n_vis = len(v_complex)
    for i in range(n_vis):
        v = v_complex[i]
        uu, vv, ww = baselines[i]

        u_idx, v_idx = uv_index(uu, vv, num_bins, uv_max)
        uv_plane[u_idx, v_idx] += v

        # Place the conjugate visibility at -uu, -vv
        u_idx, v_idx = uv_index(--uu, --vv, num_bins, uv_max)
        uv_plane[u_idx, v_idx] += np.conj(v)

    return uv_max


def rotate_vis(rot_degrees, cv, reference_positions):
    '''
        Note. This rotates counter_clockwise
        (antennas in the north move towards the east)
    '''
    conf = cv.vis.config

    new_positions = settings.rotate_location(
        rot_degrees, np.array(reference_positions).T
    )
    conf.set_antenna_positions((np.array(new_positions).T).tolist())


def image_from_calibrated_vis(cv, nw, num_bin):
    cal_syn = synthesis.Synthesis_Imaging([cv])

    cal_ift, cal_extent = cal_syn.get_ift(nw=nw, num_bin=num_bin)
    # beam = cal_syn.get_beam(nw=nw, num_bin=num_bin, use_kernel=False)
    n_fft = len(cal_ift)
    assert n_fft == num_bin

    bin_width = (max(cal_extent) - min(cal_extent)) / float(n_fft)

    return cal_ift, cal_extent, n_fft, bin_width


def get_clock_hands(timestamp):
    # ############## HOUR HAND ###########################
    #
    # The pattern rotates once every 12 hours
    #
    hour_azimuth = timestamp.hour*30.0 + timestamp.minute/2.0

    hour_sources = [{'el': el, 'az': -hour_azimuth} for el in [85, 75, 65, 55]]

    # ############## MINUTE HAND ###########################
    #
    # The pattern rotates 360 deg once every 1 hour
    #
    minute_azimuth = timestamp.minute*6.0 + timestamp.second/10.0

    minute_sources = [{'el': el, 'az': -minute_azimuth} for el in [90, 80, 70, 60, 50, 40, 30]]

    return hour_sources, minute_sources


# Helper function for testbenches
def get_clock_vis(config, timestamp):

    loc = location.Location(angle.from_dms(config.get_lat()),
                            angle.from_dms(config.get_lon()),
                            config.get_alt())

    ant_pos = config.get_antenna_positions()
    num_ant = len(ant_pos)

    ANTS = [antennas.Antenna(loc, enu=pos) for pos in ant_pos]
    ANT_MODELS = [antenna_model.GpsPatchAntenna() for i in range(num_ant)]
    RAD = radio.Max2769B(n_samples=2**12, noise_level=np.zeros(num_ant))

    hour_sources, minute_sources = get_clock_hands(timestamp)

    sim_sky = skymodel.Skymodel(0, location=loc, gps=0,
                                thesun=0, known_cosmic=0)

    for m in hour_sources + minute_sources:
        src = radio_source.ArtificialSource(loc, timestamp, r=1e6,
                                            el=m['el'], az=m['az'])
        sim_sky.add_src(src)

    sources = sim_sky.gen_photons_per_src(timestamp, radio=RAD,
                                          config=config, n_samp=1)

    v_sim = antennas.antennas_simp_vis(
        ANTS, ANT_MODELS, sources, timestamp, config, RAD.noise_level
    )

    cv = calibration.CalibratedVisibility(v_sim)

    return cv, hour_sources, minute_sources


