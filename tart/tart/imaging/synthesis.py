import pickle

import numpy as np

# import pyfftw.interfaces.numpy_fft as fft
from numpy import fft

from tart.imaging import location, radio_source
from tart.simulation import antennas
from tart.util import angle, constants

cc = np.concatenate


def get_max_ang(nw, num_bin):
    ret = np.degrees(num_bin / (4.0 * nw))
    return ret


class Synthesis_Imaging:
    def __init__(self, cal_vis_list):
        self.cal_vis_list = cal_vis_list
        self.phase_center = None
        self.grid_file = "grid.idx"
        self.grid_idx = None

    def set_grid_file(self, fpath):
        self.grid_file = fpath

    def get_uuvvwwvis_zenith(self):
        vis_l = []
        # for cal_vis in copy.deepcopy(self.cal_vis_list[:1]):
        for cal_vis in self.cal_vis_list[:1]:
            ant_p = np.array(cal_vis.get_config().get_antenna_positions())
            bls = cal_vis.get_baselines()
            pos_pairs = ant_p[np.array(bls)]
            uu_a, vv_a, ww_a = (
                pos_pairs[:, 0] - pos_pairs[:, 1]
            ).T / constants.L1_WAVELENGTH
            for bl in bls:
                ant_i, ant_j = bl
                vis_l.append(cal_vis.get_visibility(ant_i, ant_j))
        return uu_a, vv_a, ww_a, np.array(vis_l)

    def get_grid_idxs(self, uu_a, vv_a, num_bin, nw):
        try:
            if self.grid_idx is None:
                self.grid_idx = pickle.load(open(self.grid_file, "rb"))
                # print('finished loading ' + self.grid_file)
        except:
            print("generating...")
            uu_edges = np.linspace(-nw, nw, num_bin + 1)
            vv_edges = np.linspace(-nw, nw, num_bin + 1)
            grid_idx = []
            for uu, vv in zip(uu_a, vv_a):
                i = uu_edges.__lt__(uu).sum() - 1
                j = vv_edges.__lt__(vv).sum() - 1
                i2 = uu_edges.__lt__(-uu).sum() - 1
                j2 = vv_edges.__lt__(-vv).sum() - 1
                grid_idx.append([i, j, i2, j2])
            self.grid_idx = np.array(grid_idx)
            save_ptr = open(self.grid_file, "wb")
            pickle.dump(self.grid_idx, save_ptr, pickle.HIGHEST_PROTOCOL)
            save_ptr.close()
        return self.grid_idx

    def get_uvplane_zenith(self, num_bin=1600, nw=36):
        uu_a, vv_a, ww_a, vis_l = self.get_uuvvwwvis_zenith()
        arr = np.zeros((num_bin, num_bin), dtype=np.complex64)
        # place complex visibilities in the UV grid and prepare averaging by counting entries.
        grid_idxs = self.get_grid_idxs(uu_a, vv_a, num_bin, nw)
        count_arr = np.zeros((num_bin, num_bin), dtype=np.int16)

        arr[grid_idxs[:, 1], grid_idxs[:, 0]] = vis_l
        arr[grid_idxs[:, 3], grid_idxs[:, 2]] = np.conjugate(vis_l)
        n_arr = np.ma.masked_array(arr[:, :], count_arr.__lt__(1.0))
        return n_arr

    def get_uvplane(self, num_bin=1600, nw=36, grid_kernel_r_pixels=0.5):
        for cal_vis in self.cal_vis_list:
            uu_a, vv_a, ww_a = cal_vis.get_all_uvw()
            uu_a = uu_a / constants.L1_WAVELENGTH
            vv_a = vv_a / constants.L1_WAVELENGTH
            ww_a = ww_a / constants.L1_WAVELENGTH
            vis_l, bls = cal_vis.get_all_visibility()

        uu_edges = np.linspace(-nw, nw, num_bin + 1)
        vv_edges = np.linspace(-nw, nw, num_bin + 1)

        # TODO: Throw an exception if the UV-plant does not have sufficient
        # resolution to manage the baselines.

        n_arr = np.zeros((num_bin, num_bin), dtype=np.complex64)
        uu_comb = np.concatenate((uu_a, -uu_a))
        vv_comb = np.concatenate((vv_a, -vv_a))
        all_v = np.concatenate((vis_l, np.conjugate(vis_l)))
        h_real, _, _ = np.histogram2d(
            vv_comb, uu_comb, weights=all_v.real, bins=[vv_edges, uu_edges]
        )
        h_imag, _, _ = np.histogram2d(
            vv_comb, uu_comb, weights=all_v.imag, bins=[vv_edges, uu_edges]
        )
        num_entries, _, _ = np.histogram2d(
            vv_comb, uu_comb, bins=[vv_edges, uu_edges]
        )
        n_arr[:, :] = h_real + (1j * h_imag)
        pos = np.where(num_entries.__gt__(1))
        n_arr[pos] /= num_entries[pos]

        return (n_arr, uu_edges, vv_edges)

    def get_ift(self, nw=30, num_bin=2 ** 7):
        uv_plane, uu_edges, vv_edges = self.get_uvplane(
            num_bin=num_bin, nw=nw)
        ift = np.fft.fftshift(fft.ifft2(np.fft.ifftshift(uv_plane)))
        maxang = get_max_ang(nw, num_bin)
        extent = [maxang, -maxang, -maxang, maxang]
        return [ift, extent]

    def get_beam(self, nw=30, num_bin=2 ** 7):
        uv_plane, uu_edges, vv_edges = self.get_uvplane(
            num_bin=num_bin, nw=nw)
        ift = np.fft.ifftshift(fft.ifft2(np.fft.ifftshift(np.abs(uv_plane).__gt__(0))))
        return ift  # /np.sum(ret)

    def get_image(self, CAL_IFT, CAL_EXTENT):
        abs_ift = np.abs(CAL_IFT)
        ift_std = np.std(abs_ift)
        ift_scaled = abs_ift / ift_std

        plt.figure(figsize=(8, 6))
        plt.imshow(ift_scaled, extent=CAL_EXTENT)
        plt.colorbar()
        ift_median = np.median(abs_ift)
        ts = self.cal_vis_list[0].get_timestamp()
        plt.title(
            ts.strftime("%d-%m-%y %H:%M:%S")
            + " std %1.3e median: %1.3e" % (ift_std, ift_median)
        )
        plt.grid()
        plt.xlim(63, -63)
        plt.ylim(-63, 63)
        plt.xlabel("East-West")
        plt.ylabel("North-South")
        plt.tight_layout()
