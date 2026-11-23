# PRNboard

A standalone GNSS-timed PRN ionosonde exciter, intended to replace the transmit USRP and `tx_uhd.py` in [ionosonde](https://github.com/jvierine/ionosonde).

- **0.5–30 MHz**, uploaded binary phase code, **10–1000 µs chips** (default **30 µs**).
- Up to **1000 frequencies in user-defined order**, timed sweeps or single-frequency operation.
- GNSS PPS and disciplined **10 MHz TCXO**. **No qualified timing/frequency lock → no transmission.**
- **Wi-Fi and USB** configuration; stored programs run without a computer or internet.
- SMA exciter output; optional **separate protected, cooled 10 W PA**, with harmonic filtering and final 50 MHz LPF.
- Future telemetry and seven independently coded exciter outputs.

**Target: $50–100 per assembled exciter board**, using common parts with sustainable sourcing. Antenna, enclosure, adapter, cables, tax, freight, engineering, and PA are excluded. Draft components total about **$59**; PCB/assembly cost is not yet quoted.

**Current draft:** RP2040 timing/USB controller, ESP32-S3 Wi-Fi, AD9850 DDS, and stocked MAX-M10S GNSS. Any suitable dual-frequency raw-data receiver may replace the single-frequency fallback when availability and cost allow; TEC is optional.

**Status:** editable KiCad circuit and **unrouted placement study**, plus a tested host program compiler. **Not ready to order.** Routing, firmware, sourcing and RF/timing validation remain. No fabrication order has been placed.

[Revision A and remaining work](docs/revision-a.md) · [Sourcing](docs/sourcing.md) · [Requirements](docs/requirements.md)

Open `hardware/prnboard.kicad_pro` in KiCad 10.
