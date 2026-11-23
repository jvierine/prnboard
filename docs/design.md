# Preliminary design considerations

These are candidates and estimates, not a frozen design or procurement BOM.

## Architecture

Use an MCU for USB, configuration, flash, GNSS messages, and diagnostics. A small FPGA handles deterministic code playback, frequency scheduling, and hardware interlocks. A GNSS-disciplined external 10 MHz voltage-controlled TCXO supplies a clock synthesizer/distributor feeding the DDS and timing engine. PPS establishes the epoch.

The RF path is DDS → reconstruction filter → adjustable driver → hardware mute → SMA. A separate PA receives RF and a fail-safe enable signal. Locate antenna-side power sensing after the PA output filters.

The u-blox ZED-F9T-20B is a candidate timing receiver. GNSS pulse output is not automatically a substitute for a low-phase-noise oscillator; design and validate the discipline loop and clock synthesis.

AD9959 is a candidate DDS: four synchronized channels, phase modulation via profile pins, and multichip synchronization. Two devices could support seven outputs, but independent code routing, synchronization, spur performance, and 10-bit DAC limitations require review. A higher-resolution DDS or FPGA/DAC architecture remains an alternative, especially for shaped arbitrary waveforms.

## Compatibility with the existing ionosonde

The inspected upstream `tx_uhd.py` schedules timed bursts and frequency hops, controls watchdog/antenna GPIO, and checks GPS status. The inspected waveform generator also supports arbitrary phase sequences and filtered complex envelopes. Binary phase switching alone does not reproduce all such waveforms.

Before implementing a replacement, freeze representative configurations and reference waveforms, then specify sequence, pulse shaping, amplitude envelope, duty cycle, code epoch, hop guard time, and receiver delay convention. Do not assume a comment in upstream code establishes the actual waveform delay; measure the generated waveform and the physical output.

Upload exact codes rather than relying solely on random-number seeds whose interpretation may vary by implementation. A host-side configuration exporter could bridge the existing ionosonde configuration to the board without making the host necessary at runtime.

## Bandwidth and filtering

Rectangular BPSK has first spectral nulls at carrier ±1/chip_duration. A 1 µs chip therefore has a 2 MHz null-to-null main lobe. At a 0.5 MHz carrier, it is not a conventional narrowband passband signal. Define valid carrier/chip/shaping combinations and spectral acceptance limits rather than promising identical performance for every combination.

A fixed 50 MHz low-pass filter does not reject low-order harmonics of low HF carriers. A switched harmonic-filter bank is a candidate addition. Filter selection must account for occupied modulation bandwidth, insertion loss, power handling, switching transients, and mismatch.

## PA protection and cooling

Select the output device and matching network for 0.5–30 MHz performance; a transistor's ruggedness claim at one test frequency does not establish complete-amplifier open/short survival across this band. Protection must cover transients before shutdown, all relevant load phases, and retry behavior.

At an illustrative efficiency of 40–60%, 10 W RF corresponds to approximately 7–15 W of PA heat, excluding drivers and regulators. Final heatsink selection requires measured efficiency, ambient-temperature limits, and thermal resistance. Conventional USB power is insufficient for the full transmitter; consider a separate supply or negotiated USB-C PD.

## Planning costs (USD)

| Assembly | One-off prototype allowance |
| --- | ---: |
| Complete single-output exciter | $600–1,200 |
| Separate PA, filters, protection, cooling and supply | $250–600 |
| Complete system | $850–1,800 |

Tentative mature small-batch targets, roughly 10–50 units: $350–650 per exciter and $150–350 per PA assembly. A seven-output exciter was provisionally estimated at $700–1,300 in small batches. All ranges exclude engineering, test equipment, qualification, tax, shipping, and manufacturing rework; they require revision against a real BOM and assembly quote.

As a retail reference, SparkFun lists its F9T-20B timing breakout at $314.95. This is a breakout-board price, not a bare-module quote or a commitment on availability.

## Sources

- [Existing ionosonde transmitter](https://github.com/jvierine/ionosonde/blob/master/tx_uhd.py)
- [Existing waveform generator](https://github.com/jvierine/ionosonde/blob/master/create_waveform.py)
- [u-blox ZED-F9T family](https://www.u-blox.com/en/product/zed-f9t-module?legacy=Current)
- [AD9959 product information and datasheet](https://www.analog.com/en/products/ad9959.html)
- [SparkFun F9T-20B breakout](https://www.sparkfun.com/sparkfun-gnss-timing-breakout-zed-f9t-20b-qwiic.html)
