# Historical revision — superseded

The current circuit is [Revision B](revision-b.md). The following describes the earlier AD9850 draft.

# Revision A engineering draft

This is a circuit and software starting point, **not a board ready to order**. No hardware has been manufactured or measured. The KiCad PCB is an unrouted placement study and currently has layout violations. No Gerbers or fabrication release are provided.

The required continuous LFM mode added on 24 November 2026 supersedes this draft's DDS selection as a complete architecture. See [LFM requirements and candidate review](lfm.md). The original CAD remains an AD9850 review draft; it has not been converted or validated for autonomous chirping.

## Selected direction

The user confirmed on 24 November 2026 that a roughly $22 DDS is acceptable. Retain the DDS baseline and the overall $50–100 assembled-board target. A clock-generator/XOR alternative was discussed but is not selected; any future architecture change should be justified by performance or sourcing as well as cost.

| Block | Draft part | Why |
| --- | --- | --- |
| Deterministic control and USB | RP2040 + external flash | Separate waveform work from Wi-Fi; common inexpensive controller |
| Wi-Fi | ESP32-S3-WROOM-1-N8 | JLC-listed module with antenna; UART link to timing MCU |
| GNSS | MAX-M10S-00B | Stocked JLC fallback; single frequency, no dual-frequency TEC |
| Tunable reference | KDS 1XTV10000MDA + MCP4725 + TLV3501 | 10 MHz voltage-controlled TCXO with DAC and clipped-sine reshaping |
| Clock multiplier | Si5351C-B-GM | External reference input; candidate 10 MHz → 800 MHz PLL → 100 MHz DDS clock |
| DDS | AD9850BRSZ | Rated to 110 MHz at 3.3 V; 100 MHz clock supports 0.5–30 MHz output |
| Output | 35 MHz reconstruction filter, mute, OPA356, SMA | Low-power exciter; separate PA remains a later design |
| Fail-safe gate | Dual 74HC123 and LVC AND gates | Missing-PPS timeout plus independent software heartbeat timeout |

A 12 MHz crystal stays on the RP2040 so normal USB ROM recovery remains possible. The waveform timing engine must count the external disciplined reference; MCU timer delays or Wi-Fi callbacks cannot define chip timing. This architecture has not yet been proven in on-device PIO/DMA firmware.

The AD9850 serial interface requires all 40 bits for each update. At 10 Mbit/s a word takes 4 µs, which fits inside the minimum 10 µs chip, with remaining time for update and scheduling. Preload the next word, then generate FQ_UD at the scheduled reference edge. The five phase bits can represent 0° and 180° exactly. Phase changes have a specified DDS pipeline latency; measure total output delay and jitter. Preserve phase-accumulator continuity during chip updates. RF should be muted during configuration, clock acquisition, and hops.

## GNSS and TEC selection

The user permits any receiver manufacturer, and permits single-frequency fallback when an affordable, obtainable dual-frequency raw-data receiver cannot be found. Dual-band reception alone is insufficient: phase and pseudorange for two signals from the same satellite must be available.

- u-blox NEO-F10N-00B-20 has appropriate raw observations, but exact JLC stock was not established. The generic NEO-F10N listing showed zero stock and does not establish the raw-data option.
- Quectel LG290P supports multi-frequency observations through RTCM MSM; JLC listings exist, but an orderable stock quantity and price were not established in this check. LC29H's generic JLC listing showed zero stock and does not identify a qualified firmware/variant.
- Therefore MAX-M10S is the draft populated receiver, not a claim that suitable dual-frequency receivers do not exist. Keep the TEC upgrade open.
- J6 provides power, UART, PPS, and a reference-clock output for expansion. Remove R37/R38 to disconnect onboard GNSS TX/PPS before attaching external output drivers. Confirm power budget and external receiver voltage. No plug-in module footprint compatibility is assumed.

## Budget

The generated component estimate is about **$59**, excluding PCB, assembly, attrition, setup/loading fees, tax, freight, antenna, enclosure, adapter, PA, and engineering. Most line prices are allowances rather than secured quotes. The **$50–100 assembled-board target remains**, with the lower end unlikely for this first architecture. A complete JLC quotation is still required; Standard-only assembly for the chosen Wi-Fi module may materially affect small batches.

## Files and reproducibility

- Open `hardware/prnboard.kicad_pro` in KiCad 10. The schematic has local symbols and footprints; `hardware/circuit.json` records every pin/net and draft part.
- `tools/circuit.py` is the circuit source; `tools/cad.py` generates schematic sheets; `tools/board.py` creates the placement study.
- Run `conda run -n base python tools/build.py`. Set `KICAD_APP`, `KICAD_SYMBOL_DIR`, and `KICAD_FOOTPRINT_DIR` when KiCad is not at the development location. Board generation invokes KiCad's own Python to match its `pcbnew` ABI, not macOS system Python.
- The host reference compiler runs with `conda run -n base python host/program.py examples/sweep.json validation/example-program.h5`. The example code is only a demonstration, not the agreed station code.
- HDF5 is the host reference format, **not an implemented firmware upload protocol**. No deployable transmitter/Wi-Fi firmware is delivered yet.
- Run `conda run -n base python -m unittest discover -s tests -v`.

## Required before fabrication

1. Review the actual circuit against manufacturer datasheets, not only ERC. In particular verify the exact KDS footprint/underbody keepout, Si5351 exposed pad and input coupling, RF-switch truth table, USB connector, and every manufacturer package drawing. The current oscillator footprint is a placement proxy and is not approved for that part.
2. Resolve the Si5351C 10 MHz minimum input specification against oscillator pull range and tolerance. Verify input levels/coupling and jitter. If necessary change the clock architecture; do not silently operate outside the datasheet.
3. Complete placement, Wi-Fi antenna clearance, controlled RF routing, solid ground returns, decoupling, USB routing, and all-layer DRC. Current PCB has unconnected nets and overlaps; it cannot be manufactured as a working board.
4. Freeze real resistor/capacitor/inductor part numbers and RF Q/self-resonance, not merely nominal values. Model the actual filter and driver/load response. The requested 50 MHz power-output LPF and HF harmonic bank belong to the separate PA.
5. Confirm continuous and peak current, regulator dissipation, USB power negotiation, bulk decoupling, and host-port current limits. A 5 V adapter rated at least 1 A is a provisional bench supply requirement; do not assume an unconfigured USB host permits the full board load.
6. Implement and test MCU clock observation/discipline, PPS-to-UTC association, validated persistent configuration, code feeding, frequency timing, USB recovery, and authenticated local Wi-Fi control. Firmware heartbeat must come from a fresh health check and stop on stale GNSS data or a waveform-engine fault; an autonomous heartbeat must not hide a stalled CPU.
7. Measure hardware mute on boot, reset, stale GNSS, missing PPS, software failure, clock fault and PA fault. Characterize HC123 timeouts with actual R/C tolerances, leakage and temperature; nominal timing is not an acceptance guarantee.
8. Obtain a dated BOM/assembly quote, recheck exact stock/variants, and perform a full release review. No order is authorized or placed by this draft.

## Evidence

KiCad schematic ERC: zero findings at the draft checkpoint. Footprint pin-number check: zero missing or unmapped pads. The seven host compiler tests and ten additional integration tests pass. A [reference-model end-to-end test](end-to-end.md) also exercises RF acquisition and the existing upstream PRN decoding functions on synthetic samples. These checks do not validate timing, RF behavior, physical footprint suitability, firmware, or hardware safety. Detailed reports are under `validation/`.
