
from tart.imaging import imaging

import numpy as np
import matplotlib.pyplot as plt
import requests
import numpy.fft as fft

API_SERVER = 'https://api.elec.ac.nz/tart/tart-kenya'

def get_api(api):
    url = f"{API_SERVER}/api/v1/{api}"
    print(f"Try it yourself: {url}")
    response = requests.get(url)
    return response.json()

print(f"Downloading data from {API_SERVER}")
mode = get_api('mode/current')

if mode['mode'] != 'vis':
    print("ERROR: Telescope must be in visibility mode to allow imaging. Set via the web API")


gains = get_api('calibration/gain')
visibility_data = get_api('imaging/vis')
ant_pos = get_api('imaging/antenna_positions')
ant_pos = np.array(ant_pos)

print(f"Visibilities time: {visibility_data['timestamp']}")
gains_complex = np.array(gains['gain']) * np.exp(1.0j*np.array(gains['phase_offset']))
wavelength = 2.99793e8 / 1.57542e9   # wavelength is speed of light / frequency

num_vis = len(visibility_data)
v_calib = np.zeros(num_vis, dtype=np.complex64)
baselines = np.zeros((num_vis, 3), dtype=np.float32)

for k in range(num_vis):
    v = visibiity_data[k]
    v_complex = v['re'] + v['im']*1.0j
    i = v['i']
    j = v['j']
    v_calib[k] = imaging.apply_complex_gains(v_complex, gains_complex, i, j)
    v['cal'] = v_calib

    # Work out the baselines
    baselines[k, :] = imaging.ant_pos_to_uv(ant_pos, i, j) / wavelength

N_FFT = 256
uv_plane = np.zeros((N_FFT, N_FFT), dtype=np.complex64)

uv_max = imaging.grid_visibility(uv_plane, v_calib, baselines)

plt.figure(figsize=(4, 3), dpi=N_FFT/6)
plt.title("U-V plane image")

plt.imshow(np.abs(uv_plane), extent=[-uv_max, uv_max, -uv_max, uv_max])

plt.xlim(-uv_max, uv_max)
plt.ylim(-uv_max, uv_max)
plt.savefig('uv_plane.jpg')
plt.show()



cal_ift = np.fft.fftshift(fft.ifft2(np.fft.ifftshift(uv_plane)))

# Take the absolute value to make an intensity image
img = np.abs(cal_ift)
# Scale it to multiples of the image standard deviation
img /= np.std(img)


# Step 5. Plot the image

plt.figure(figsize=(4, 3), dpi=N_FFT/4)
plt.title("Inverse FFT image")

print("Dynamic Range: {}".format(np.max(img)))

plt.imshow(img, extent=[-1, 1, -1, 1])

plt.xlim(-1, 1)
plt.ylim(-1, 1)
cb = plt.colorbar()
plt.savefig('basic_image.jpg')
plt.show()
