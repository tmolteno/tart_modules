import numpy as np

try:
    from pylab import plot, show, subplot, xlabel, ylabel

    PYLAB_AVAILABLE = True
except ImportError:
    PYLAB_AVAILABLE = False

import numpy.fft as fft


def getSpectrum(y, Fs):
    """
    Get a Single-Sided Amplitude Spectrum of y(t)
    """

    n = len(y)  # length of the signal
    k = np.arange(n)
    T = n / Fs
    frq = k / T  # two sides frequency range
    frq = frq[list(range(n // 2))]  # one side frequency range

    Y = fft.fft(y) / n  # fft computing and normalization
    Y = Y[list(range(n // 2))]

    return (frq, np.array(abs(Y)))


def plotSpectrum(y, Fs, c="red", label="powerspectrum", doPlot=False):
    """
    Plots a Single-Sided Amplitude Spectrum of y(t)
    """
    if not PYLAB_AVAILABLE:
        raise ImportError(
            "matplotlib/pylab is required for plotSpectrum. Install with: pip install matplotlib"
        )

    frq, absY = getSpectrum(y, Fs)

    plot(frq, absY, c=c, label=label)  # plotting the spectrum
    xlabel("Freq (Hz)")
    ylabel("|Y(freq)|")
    return (frq, absY)


if __name__ == "__main__":
    if not PYLAB_AVAILABLE:
        print("matplotlib/pylab is required for plotting examples")
        exit(1)

    Fs = 150.0
    # sampling rate
    Ts = 1.0 / Fs
    # sampling interval
    t = np.arange(0, 1, Ts)  # time vector

    ff = 5
    # frequency of the signal
    y = np.sin(2 * np.pi * ff * t)

    subplot(2, 1, 1)
    plot(t, y)
    xlabel("Time")
    ylabel("Amplitude")
    subplot(2, 1, 2)
    plotSpectrum(y, Fs)
    show()
