## Utility functions for imaging
import numpy as np

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
    uv_max = num_bins / (np.pi)

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

