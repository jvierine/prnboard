# Preliminary design considerations

These are candidates and estimates, not a frozen design or procurement BOM.

## Architecture

The baseline is cost-first: one inexpensive USB MCU with deterministic peripheral-driven output (PIO/timers plus DMA), one single-channel DDS, a standard u-blox GNSS receiver with PPS, and an external voltage-controlled 10 MHz TCXO with a simple discipline loop. No FPGA, premium timing receiver, or populated multichannel hardware in the initial board.

RP2040/RP2350-class controllers are candidates. Code transitions must run from the disciplined clock domain, not an unrelated MCU crystal. Prove a supported external-clock arrangement and legal clock rates before selecting the MCU. Hardware-timed phase selection avoids per-chip USB traffic or firmware interrupt timing. USB configuration, flash storage, GNSS parsing, and diagnostics remain on the MCU.

MAX-M10S-class u-blox PPS receivers are candidates; final part selection depends on genuine-module price and assembly availability. Validate PPS uncertainty, time validity reporting, and discipline performance against receiver requirements rather than buying nanosecond timing specifications by default. The external oscillator must have an accessible voltage-control input: a fixed TCXO alone cannot implement this discipline loop.

A single-channel DDS with a hardware phase-select input is preferred. AD9834 is a feasibility candidate, not a selected part: its 75 MHz clock leaves limited reconstruction-filter margin at 30 MHz, so verify full-band spectral performance and price before committing. A faster economical DDS is an alternative. Do not substitute AD9833 without checking its frequency ceiling. Keep the RF driver modest and defer the exact output-level target until a real BOM is available.

The RF path is DDS → reconstruction filter → driver → fail-safe RF mute → SMA. A separate PA receives RF and an enable signal. Retain a hardware missing-PPS/watchdog inhibit; cost reduction does not remove the lock requirement. GNSS validity still requires fresh protocol status as well as pulse detection.

Seven outputs are a later hardware revision. Preserve configuration/protocol extensibility and sensible synchronization access without paying for extra DDS channels, drivers, or an FPGA now.

## Sourcing policy

Choose common active-production parts with multiple established authorized stocking distributors and verify JLCPCB/LCSC assembly availability before layout release. Prefer standard packages and documented substitutes for commodity circuitry. Specialized DDS, GNSS, and tunable oscillator parts need explicit lifecycle and supply review; the named candidates above have not passed that review. Avoid a design dependent on surplus modules, marketplace clones, or a single transient stock listing. Retain dated sourcing evidence in the eventual BOM and recheck before ordering.

## Compatibility with the existing ionosonde

The inspected upstream `tx_uhd.py` schedules timed bursts and frequency hops, controls watchdog/antenna GPIO, and checks GPS status. The inspected waveform generator also supports arbitrary phase sequences and filtered complex envelopes. Binary phase switching alone does not reproduce all such waveforms.

Before implementing a replacement, freeze representative configurations and reference waveforms, then specify sequence, pulse shaping, amplitude envelope, duty cycle, code epoch, hop guard time, and receiver delay convention. Do not assume a comment in upstream code establishes the actual waveform delay; measure the generated waveform and the physical output.

Upload exact codes rather than relying solely on random-number seeds whose interpretation may vary by implementation. A host-side configuration exporter could bridge the existing ionosonde configuration to the board without making the host necessary at runtime.

## Bandwidth and filtering

Rectangular BPSK has first spectral nulls at carrier ±1/chip_duration. At the minimum supported chip duration of 10 µs, the first nulls are ±100 kHz from the carrier (200 kHz null-to-null). At the default 30 µs, they are approximately ±33.3 kHz (66.7 kHz null-to-null). Spectral sidelobes extend beyond these nulls; define pulse shaping and spectral acceptance limits across the carrier range. The supported chip-duration range is 10–1000 µs.

A fixed 50 MHz low-pass filter does not reject low-order harmonics of low HF carriers. A switched harmonic-filter bank is a candidate addition. Filter selection must account for occupied modulation bandwidth, insertion loss, power handling, switching transients, and mismatch.

## PA protection and cooling

Select the output device and matching network for 0.5–30 MHz performance; a transistor's ruggedness claim at one test frequency does not establish complete-amplifier open/short survival across this band. Protection must cover transients before shutdown, all relevant load phases, and retry behavior.

At an illustrative efficiency of 40–60%, 10 W RF corresponds to approximately 7–15 W of PA heat, excluding drivers and regulators. Final heatsink selection requires measured efficiency, ambient-temperature limits, and thermal resistance. Conventional USB power is insufficient for the full transmitter; consider a separate supply or negotiated USB-C PD.

## Cost target (USD)

**User target: $50–100 per assembled single-channel exciter board.** Budget for a small batch (provisionally 10–50 boards), with onboard GNSS and 10 MHz oscillator discipline. These are allocation ceilings, not quoted component prices:

| Function | Target allocation per board |
| --- | ---: |
| Genuine standard u-blox PPS module | $12–22 |
| USB MCU, flash, digital support | $3–6 |
| Single-channel DDS | $8–18 |
| Voltage-controlled TCXO, discipline and clock circuitry | $6–12 |
| RF filtering, modest driver, mute and SMA | $6–12 |
| Regulators, USB, passives and protection | $4–8 |
| PCB and assembly allocation | $8–18 |
| Total allocated range | $47–96 |

The $100 ceiling is the initial acceptance target; $50 is the stretch target. The upper allocation leaves little contingency. Verify genuine GNSS/DDS sourcing and JLCPCB assembly charges first, then adjust the architecture if it does not fit. Do not report this as an achieved manufacturing cost. One-off bring-up, minimum order quantities, setup fees, and respins can exceed the per-board target.

Excluded: GNSS antenna, enclosure, cables, power adapter, shipping, tax, engineering, test equipment, qualification, and separate PA. The PA requires its own costed design; the $50–100 exciter target is not a promise for the complete 10 W transmitter. Earlier premium-receiver/FPGA prototype estimates are superseded by this cost-first baseline.

## Sources

- [Existing ionosonde transmitter](https://github.com/jvierine/ionosonde/blob/master/tx_uhd.py)
- [Existing waveform generator](https://github.com/jvierine/ionosonde/blob/master/create_waveform.py)
- [u-blox ZED-F9T family](https://www.u-blox.com/en/product/zed-f9t-module?legacy=Current)
- [AD9959 product information and datasheet](https://www.analog.com/en/products/ad9959.html)
- [u-blox MAX-M10 family](https://www.u-blox.com/en/product/max-m10-series?legacy=Current)
- [AD9834 DDS](https://www.analog.com/en/products/ad9834.html)
- [RP2350 pricing and hardware overview](https://www.raspberrypi.com/news/rp2350-now-available-to-buy-a-high-performance-secure-microcontroller-for-your-next-project/)
