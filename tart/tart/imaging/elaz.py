#
# An object that represents a location in the Elevation and Azimuth, and
# handles projection into the l,m plane.
#
# Azimuth is measured clockwise from north (y - axis)
# Tim Molteno 2017-2019
#
import numpy as np

from tart.util.angle import wrap_180


class ElAz:
    def __init__(self, el, az):

        self.el = el
        self.az = wrap_180(az)
        self.el_r = np.radians(self.el)
        self.az_r = np.radians(self.az)

        # l,m are the cosines of the angle between the source vector and the
        # u and v axes respectively.
        self.l = -np.sin(self.az_r) * np.cos(self.el_r)
        self.m = np.cos(self.az_r) * np.cos(self.el_r)
        self.n = np.sin(self.el_r)

    def get_lm(self):
        return self.l, self.m

    def __repr__(self):
        return f"tart.imaging.ElAz(el={self.el:5.2f}, az={self.az:5.2f})"

    '''
        Return the area of a unit-solid area of source dS
        in the l,m plane
    '''
    def get_lm_area(self, dS=1.0):
        return dS * np.sqrt(1.0 - self.l * self.l - self.m * self.m)

    def get_px(self, num_bins):
        ''' Get source location in pixels from it's direction
            cosines. These should be image coordinates in an
            image num_bins x num_bins essentially used as array
            indices.
        '''
        n2 = num_bins // 2
        x_px = int(np.round(self.l * n2 + n2))
        y_px = num_bins - int(np.round(self.m * n2 + n2))
        return x_px, y_px

    def deg_to_pix(self, num_bins, deg):
        pix_per_rad = num_bins / np.pi
        d = np.radians(deg) * pix_per_rad / 2
        return d

    @classmethod
    def from_pixels(cls, x_pix, y_pix, num_bins):
        ''' Create from pixel coordinates. The center (0,0) is
            in the middle.
        '''
        # print(f"from_pixels({x_pix}, {y_pix})")
        n2 = num_bins // 2
        x = x_pix - n2
        y = num_bins - y_pix - n2    # y_px = num_bins - int(np.round(self.m * n2 + n2))
                                     # num_bins - y_px - n2 =  mn2
                                     # num_bins - y_px - n2 =  mn2
        # print(f"centred_pixels({x}, {y})")
        r = np.sqrt(x*x + y*y)
        # print(f"r=({r}, {n2})")

        if r < n2:
            el_r = np.arccos(r/n2)
        else:
            el_r = 0.0
        # print(f"    el_r = {el_r}")
        atn = np.arctan2(y, x)
        # print(f"    atn = {np.degrees(atn)}")
        az_r = atn - np.radians(90)
        # print(f"    az_r = {az_r}")

        return ElAz(np.degrees(el_r), np.degrees(az_r))

    def get_px_window(self, num_bins, window_deg):
        ''' Get a pixel window around a source with width window_deg
            This is assumed to be an inverse FFT image with num_bins x num_bins
        '''
        x_i, y_i = self.get_px(num_bins)

        d = self.deg_to_pix(num_bins, window_deg)

        x_min = int(np.floor(x_i - d))
        x_max = int(np.ceil(x_i + d))
        y_min = int(np.floor(y_i - d))
        y_max = int(np.ceil(y_i + d))
        area = (x_max - x_min) * (y_max - y_min)
        return x_min, x_max, y_min, y_max, area

    def get_old_lm(self):
        R = 10 * np.pi * 2
        r = 90 - np.degrees(self.el_r)
        r = R * np.arctan(r / R)
        x = r * np.sin(self.az_r)
        y = r * np.cos(self.az_r)
        return [-x, y]


def from_json(source_json, el_limit=0.0, jy_limit=1e5):
    src_list = []

    for src in source_json:
        try:
            if (src["el"] > el_limit) and (src["jy"] > jy_limit):
                src_list.append(ElAz(src["el"], src["az"]))
        except:
            print(f"ERROR in catalog src={src}")

    return src_list


def get_source_coordinates(source_list):
    x_list = []
    y_list = []

    for src in source_list:
        x_list.append(src.l)
        y_list.append(src.m)

    return [x_list, y_list]
