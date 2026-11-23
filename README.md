# PRNboard

A planned standalone, GNSS-timed DDS exciter for PRN ionosondes and coded-CW radar. Intended to replace the transmitter USRP and `tx_uhd.py` in [jvierine/ionosonde](https://github.com/jvierine/ionosonde).

- Configurable carrier: initially **0.5–30 MHz**.
- User-uploaded binary phase code; **30 µs chips by default**, configurable from **10–1000 µs**.
- UTC-aligned frequency programs: up to **1000 frequencies in user-defined order**, or single-frequency operation.
- Dual-frequency u-blox GNSS with raw carrier phase/pseudorange for **TEC**, PPS-defined time, and a disciplined **10 MHz TCXO**. Preferred candidate: **NEO-F10N-00B-20** (raw-data variant).
- **No valid GNSS timing or oscillator lock → no transmission.**
- Prefer common, active-production components stocked by multiple established suppliers; check JLCPCB/LCSC availability before release.
- USB configuration and power; programs stored onboard; no computer or internet required during operation.
- SMA exciter output. Separate optional **10 W PA**, with cooling, open/short protection, harmonic filtering, and a final **50 MHz low-pass filter**.
- Provision for later telemetry; **seven independently coded outputs** are a future revision, not populated on the first board.

**Status:** requirements and feasibility only. No schematic, PCB, firmware, or validated BOM yet. A future revision is intended for JLCPCB manufacture and bench testing; no fabrication is planned now.

**Cost target: US$50–100 per assembled single-channel exciter board** in a small batch. This includes onboard GNSS and clock discipline, but excludes the GNSS antenna, enclosure, cables, power adapter, shipping, tax, engineering, and the separate PA. This is a design target, not a validated BOM or quote.

Cost-first direction: one inexpensive USB microcontroller with hardware-timed code output, one DDS, a dual-frequency raw-data u-blox receiver, and a disciplined 10 MHz voltage-controlled TCXO. No FPGA or premium timing receiver in the baseline.

See [requirements](docs/requirements.md) and [design considerations](docs/design.md) for details and unresolved decisions.
