# Continuous LFM

Revision B selects AD9954 with a 200 MHz system clock. The host compiler emits saved HDF5 register programs; a separate serial decoder and integer phase-accumulator model reload and test them. This is a reference implementation, not running MCU firmware or a hardware measurement.

| Requested rate (Hz/s) | Achieved rate (Hz/s) | Rate error (ppm) | Frequency step (Hz) | Update interval (µs) |
| ---: | ---: | ---: | ---: | ---: |
| 100000 | 99988.619974 | −113.800 | 0.325963 | 3.26 |
| 500000 | 500038.966236 | +77.932 | 1.490116 | 2.98 |

The ramp changes frequency in sub-2 Hz steps without resetting accumulated phase. The receiver must use the exported achieved rate, rather than silently assuming the nominal requested value. The compiler currently allows 200 ppm rate error and 2 Hz maximum steps; these are provisional engineering limits. It supports ascending sweeps and an explicit endpoint tone hold. Automatic repeat/return chirps are not implemented.

Full 0.5–30 MHz sweeps take about 295.034 s and 58.9954 s. Tests evaluate exact integer phase evolution across the full span, update boundaries and endpoint hold, then dechirp a noisy echo with 1 ms delay and 25 Hz Doppler against an independent quadratic-phase reference. Both cases pass: beat errors below 0.001 Hz, phase ripple below 4 µrad in the ideal digital model. A deliberately wrong receiver rate is rejected. The PRN fault suite separately checks common transmit interlocks; the LFM model does not execute firmware or prove hardware shutdown.

The phase-origin model assumes SYNC_CLK-aligned PS0, the documented 28-clock latency and first-delta seed. These assumptions need oscilloscope validation. PLL phase noise, TCXO accuracy, DAC nonlinearity, analog spurs and filtering are excluded from the LFM phase test. The PRN RF model includes ideal DAC quantization and the nominal output filter, not measured spectral purity.

Numerical evidence is in `validation/lfm/results.h5` and `summary.json`; run all reference tests with `conda run -n base python simulation/run_all.py`.
