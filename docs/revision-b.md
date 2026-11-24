# Revision B — AD9954 exciter

The current circuit replaces AD9850 and Si5351C with AD9954YSVZ-REEL7. Its internal ×20 PLL derives 200 MHz from the disciplined 10 MHz reference. PRN uses the 14-bit phase register; LFM uses autonomous frequency accumulation with phase-clear disabled.

The schematic includes separate 1.8 V analog/digital regulators, 3.3 V digital IO, per-rail bypass capacitors, a 243 Ω / 10 nF PLL loop network, and an attenuated AC-coupled reference input. The unused reference input is bypassed to AVDD. DAC current-sink loads return to AVDD, including the filter termination; output is AC coupled. RSET is 3.92 kΩ. These changes follow the [manufacturer datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9954.pdf).

RP2040 GPIO20 controls PS0, GPIO21 receives SYNC_CLK, GPIO28 controls chip select and GPIO29 receives SDO. IO_UPDATE must be synchronized to SYNC_CLK. There is no dedicated PLL lock output; settling and clock qualification need firmware and bench validation. The 50 MHz SYNC_CLK input path needs timing verification. Old host-format programs are incompatible: PRN format version 2 stores separate frequency and phase writes and explicit PLL configuration.

This remains an unrouted placement study. ERC and connectivity checks do not establish signal integrity, reference quality, thermal margin, emissions or fabrication readiness. Firmware, routing, clock alignment, RF spectra, timing-lock loss tests and physical receiver-loopback tests remain required. No boards have been ordered.
