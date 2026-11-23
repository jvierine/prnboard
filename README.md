# PRNboard

A planned standalone, GNSS-timed DDS exciter for PRN ionosondes and coded-CW radar. Intended to replace the transmitter USRP and `tx_uhd.py` in [jvierine/ionosonde](https://github.com/jvierine/ionosonde).

- Configurable carrier: initially **0.5–30 MHz**.
- User-uploaded binary phase code; **30 µs chips by default**, configurable from **1–1000 µs**.
- UTC-aligned frequency programs: up to **1000 frequencies in user-defined order**, or single-frequency operation.
- u-blox GNSS timing, PPS-defined time, and a disciplined **10 MHz TCXO**.
- **No valid GNSS timing or oscillator lock → no transmission.**
- USB configuration and power; programs stored onboard; no computer or internet required during operation.
- SMA exciter output. Separate optional **10 W PA**, with cooling, open/short protection, harmonic filtering, and a final **50 MHz low-pass filter**.
- Provision for later telemetry and **seven independently coded exciter outputs**.

**Status:** requirements and feasibility only. No schematic, PCB, firmware, or validated BOM yet. A future revision is intended for JLCPCB manufacture and bench testing; no fabrication is planned now.

Initial planning budget: **US$600–1,200 for a one-off exciter**, plus **$250–600 for the PA assembly**. These are unquoted estimates, excluding engineering, tax, and shipping.

See [requirements](docs/requirements.md) and [design considerations](docs/design.md) for details and unresolved decisions.
