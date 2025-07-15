## Utility functions for imaging
import numpy as np

from tart.imaging import synthesis
from tart.operation import settings


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
