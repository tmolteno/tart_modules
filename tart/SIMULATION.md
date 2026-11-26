# Simulating a TART observation from an external 1.575 GHz time series

The `tart.simulation` module models the TART receiver (a MAX2769B GPS
front-end) and can turn an externally simulated RF time series into a TART
observation file.

## The pipeline

`Max2769B` (in `tart/simulation/radio.py`) models the receiver as:
mix with a 1571.328 MHz LO → IF at 4.092 MHz → anti-alias filter →
decimate → 2.5 MHz bandpass → 1-bit NRZ quantizer, with output sampled at
`ref_freq` = 16.368 MHz.

The entry point for an externally generated RF signal is
`rad.get_full_obs(ant_sigs, utc_date, config, timebase)`. It expects:

- `ant_sigs`: a real-valued numpy array of shape `(num_ant, N)` — one RF
  time series per antenna, at 1.57542 GHz.
- The signal must be sampled at the radio's full rate
  `rad.sampling_rate = ref_freq * freq_mult` (16.368 MHz × 256 ≈ 4.19 GHz
  by default), spanning `rad.sample_duration` seconds. If your external
  simulation uses a different rate, resample to this first.
- A `config` (`tart.operation.settings`) that defines the telescope and the
  number of antennas.

## Example

```python
import numpy as np

from tart.operation import observation, settings
from tart.simulation.radio import Max2769B
from tart.util import utc

# Telescope configuration (defines number of antennas, positions, sampling).
# For a real telescope this JSON comes from the /info API endpoint.
config = settings.from_file("./tart/test/test_telescope_config.json")
num_ant = config.get_num_antenna()

# 1. Create the radio model. noise_level is the per-antenna noise std-dev
#    added at baseband (use 0.0 to disable).
n_samples = 2**15                       # output samples per antenna
noiselvls = 0.1 * np.ones(num_ant)
rad = Max2769B(noise_level=noiselvls, n_samples=n_samples)

# 2. Your externally simulated 1.57542 GHz time series, one row per
#    antenna, sampled at rad.sampling_rate over rad.sample_duration.
timebase = np.arange(0, rad.sample_duration, 1.0 / rad.sampling_rate)
ant_sigs = np.array([
    np.cos(2 * np.pi * 1575.42e6 * timebase + phase)
    for phase in np.linspace(0.0, np.pi, num_ant)
])

# 3. Run each antenna signal through the radio model. This mixes with the
#    LO, filters, decimates to 16.368 MHz and quantizes to 1-bit, then
#    wraps the result in an Observation object.
obs = rad.get_full_obs(ant_sigs, utc.now(), config, timebase)

# 4. Write the raw data file in the TART HDF5 format.
obs.to_hdf5("sim_obs.h5")

# Load it back later:
obs2 = observation.Observation_Load("sim_obs.h5")
data = obs2.get_antenna(0)     # bipolar ±1 array at 16.368 MHz
```

## Notes

- For per-antenna control (e.g. a different `sample_duration` or to silence
  the debug prints), call
  `rad.sampled_signal(ant_sig, ant_index, sample_duration, debug=False)`
  yourself and build the observation directly, mirroring what
  `get_full_obs` does:

  ```python
  sampled = np.array([rad.sampled_signal(ant_sigs[i], i, rad.sample_duration, debug=False)
                      for i in range(num_ant)])
  sampled = np.asarray((sampled + 1) / 2, dtype=bool)   # unipolar boolean
  obs = observation.Observation(utc.now(), config=config, data=sampled)
  obs.to_hdf5("sim_obs.h5")
  ```

- The observation file is HDF5 (`.h5`), the raw data format used by the
  TART package. It contains three datasets: `config` (the telescope
  configuration JSON), `timestamp` (ISO format) and `data` (one bit per
  sample, packed with `np.packbits`, one row per antenna), so files are
  compact. `Observation_Load` accepts both `.h5` and `.hdf` extensions.
- The test `tart/simulation/test/test_radio.py` shows the same flow using
  tart's own `antennas.antennas_signal()` generator instead of an external
  signal — useful as a reference for matching amplitude/delay conventions
  if you want inter-antenna phase delays consistent with a source at a
  given azimuth/elevation.
- The "full" path is computationally heavy because of the ~4 GHz input
  rate. If you only need the signal at baseband/IF,
  `rad.get_simplified_obs` accepts complex baseband signals on the
  16.368 MHz timebase instead, skipping the GHz-rate simulation entirely.
