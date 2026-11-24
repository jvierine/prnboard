# Firmware status

No flashable transmitter or Wi-Fi firmware is implemented yet. `host/program.py` is a host reference compiler, not a hardware driver.

The draft separates a USB/timing RP2040 from an ESP32-S3 Wi-Fi module over UART. RP2040 GPIO assignments are explicit in `tools/circuit.py`; use UART0 for Wi-Fi, UART1 for GNSS, and I2C1 for the DAC and clock generator.

Required implementation sequence:

1. Boot with TX_REQUEST and QUALIFIED low. Configure the missing-PPS/heartbeat gates and monitor the actual TX_ENABLE feedback.
2. Configure GNSS 1 PPS and decode fresh validity, UTC and pulse-associated time messages. Establish the epoch correctly across rollover and leap events.
3. Configure the external-reference clock multiplier while muted. Characterize the oscillator tuning curve, close a slow discipline loop, and qualify timing/frequency lock before arming.
4. Prove reference-edge counting and PPS-aligned code playback in PIO/DMA. Preload AD9954 register writes and latch them at scheduled chip edges. Detect stalls/underruns and mute immediately. Account for the DDS pipeline and output path delay.
5. Load checked persistent programs and execute frequency order/dwell/repeat scheduling. Mute during the end-of-dwell guard, truncate a final chip at the mute boundary if necessary, and restart the code at chip zero at each new frequency. Single-frequency mode repeats the code continuously until stopped or inhibited.
6. Generate the hardware watchdog heartbeat from a running health check only while GNSS status, PPS, oscillator lock, waveform feeding, program integrity and PA status are valid. A free-running peripheral heartbeat is prohibited because it can mask a crashed health loop.
7. Add bounded UART commands, authenticated local Wi-Fi setup/control, atomic program updates, diagnostics, and USB recovery. Network failure must not disturb a valid standalone program. Network commands cannot override the interlock.
8. Verify every inhibit path and schedule transition on physical hardware before transmitting through a PA.

The HDF5 host program has 100 ns reference ticks, explicit binary code, a frequency table and a 40-bit frequency register write and two 24-bit phase register writes per frequency (format version 2). Firmware needs a bounded binary upload representation; it should not parse HDF5 on the MCU. Translate and checksum the validated host representation when that protocol is defined. Do not treat the example code or UTC epoch zero as an operational station configuration.

Revision B uses a 200 MHz AD9954 clock from the internal ×20 PLL. Initialize 1.8 V core / 3.3 V IO, CFR1 and CFR2 before playback. IO_UPDATE and PS0 require alignment to SYNC_CLK; frequency/phase and ramp latencies are respectively 24 and 28 system-clock cycles. The reference model assumes alignment; firmware must demonstrate it on hardware. LFM uses the autonomous ramp engine, with phase-clear disabled and endpoint hold. No executable MCU firmware exists yet.
