# Continuous LFM requirement and DDS review

The board must generate continuous, phase-continuous LFM at typical slopes of **100 kHz/s** and **500 kHz/s**, in addition to its original PRN mode. This is an architecture requirement, not a feature already implemented by the AD9850 draft or verified by the PRN simulation.

## Signal and timing

The ideal phase is φ(t) = φ0 + 2π[f_start t + k t²/2]. Do not clear the phase accumulator while sweeping. The RF output must remain enabled throughout a valid chirp, with deterministic GNSS-referenced timing and the existing fault inhibit.

For 0.5–30 MHz the span is 29.5 MHz, so sweep durations are 295 s and 59 s respectively. A 295 s sweep leaves only 5 s in a 300 s schedule for any separately defined return or guard operation. Endpoint behavior is unresolved: continuous up/down sweeps can preserve frequency/phase at the turn while changing slope; a sawtooth return necessarily jumps in frequency. Do not label that return frequency-continuous.

## Architecture consequence

An AD9850 can accept phase-continuous frequency updates, but it has no autonomous ramp engine. The original 10 Mbit/s MCU feed and 40-bit words require at least 4 µs per update. That is not a demonstrated implementation of the newly requested smooth continuous LFM mode.

AD9954 and AD9910 are candidate families with autonomous frequency-ramp engines. AD9954 has a 14-bit DAC and an 8-bit sweep timer; AD9910 has a more flexible digital ramp generator. Neither part is selected yet. Verify exact register semantics, clock tree, low-slope quantization, PRN capability in its separate mode, supplies, footprint, current, availability and total board cost before changing the CAD.

A ramp engine still changes its digital frequency in finite increments. The relevant question is whether its phase/rate error and dechirped products satisfy the receiver requirement, not whether its marketing description says linear sweep.

## Quantization matters

For a 32-bit frequency word, system clock f_s, delta word D, and a timer interval of R cycles of f_s/4, the achieved slope is k_actual = D f_s² / (4 · 2³² · R). Timer encodings and valid values must be checked against the selected device; this expression alone is not a register image.

Illustrative AD9954-style calculations at a nominal 200 MHz system clock, searching integer R = 1…255 and the nearest positive D:

| Requested slope | D | R | Frequency increment | Update interval | Achieved slope | Rate error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100,000 Hz/s | 7 | 163 | 0.325963 Hz | 3.26 µs | 99,988.620 Hz/s | −113.80 ppm |
| 500,000 Hz/s | 32 | 149 | 1.490116 Hz | 2.98 µs | 500,038.966 Hz/s | +77.93 ppm |

These are calculations, not selected settings or measured performance. They demonstrate that small frequency steps do not guarantee the exact requested slope. The clock rate and ramp choice must be optimized together, or a different engine selected. The receiver must use the achieved slope; no chirp-rate tolerance has yet been specified. No claim is made here that these settings are acceptable for dechirping.

## Required validation before acceptance

1. Test the actual programmed control words, ramp direction and accumulator behavior through a device-specific model. Bound phase residual relative to a quadratic-phase reference; do not reset or refit phase independently at every update and thereby hide discontinuities.
2. Check full 59 s and 295 s sweeps with an efficient integer/event model, plus representative sample-level windows across the band. Report which samples/events were actually simulated.
3. Dechirp using an independent reference with explicit clock/rate error; measure residual frequency, phase ripple and spurs. Include deliberately wrong ramp words and forced phase clears as negative controls.
4. Inject a known propagation delay and Doppler. Verify the correct beat-frequency convention and calibrated signal-path delay; do not equate fine FFT bins with validated range resolution.
5. Exercise endpoint handling and timing/frequency-lock loss. Then repeat the essential checks on real firmware and hardware with a synchronized reference receiver.

The $50–100 board target remains a constraint. A revised BOM and assembly quote are required; the old $59 component estimate does not include a replacement chirp engine.

## Manufacturer sources

- [AD9954 datasheet: sweep timer, frequency and phase accumulators, and ramp registers](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9954.pdf)
- [ADI explanation of phase continuity during AD9954 sweeps](https://ez.analog.com/data_converters/dds/f/q-a/29270/driver-for-ad9954-evaluation-board/74306)
- [AD9910 datasheet: digital ramp generator](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9910.pdf)
