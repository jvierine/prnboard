# Requirements

This records the intended device, not verified hardware performance.

## Cost

- Aim for **US$50–100 per assembled single-channel exciter board** in a small batch, including onboard GNSS and oscillator discipline. $100 is the initial ceiling; $50 is the stretch target.
- Exclude antenna, enclosure, cables, adapter, shipping, tax, engineering, and separate PA. Validate with a sourced BOM and assembly quote before claiming compliance.
- Use a cost-first MCU/DDS architecture; FPGA and premium GNSS timing receiver are not baseline requirements. Seven-channel population is deferred.

## Component availability and lifecycle

- Prefer widely used, common components in active production, with broad distribution and a credible long-term supply outlook. Avoid obsolete, end-of-life, not-recommended-for-new-design, scarce, or marketplace-only parts.
- Prefer parts stocked by multiple established authorized distributors. For JLCPCB assembly, check the actual JLCPCB/LCSC assembly catalogue and stock; prefer commonly stocked standard assembly parts where practical.
- Use standard packages and generic passives, regulators, logic, and connectors with documented compatible alternatives where possible. Verify pinout, ratings, timing, RF behavior, and firmware compatibility before approving substitutes.
- For specialized parts such as the DDS, GNSS module, and voltage-controlled TCXO, assess manufacturer lifecycle status, distributor stock, lead time, package availability, and substitution options before committing the schematic or layout. Multiple distributors do not make a single-source IC second-sourced.
- Record manufacturer part numbers, sourcing options, approved alternatives, and dated stock/lifecycle checks in the eventual BOM. Recheck before each fabrication order; current stock cannot guarantee future availability.
- Existing named components are feasibility candidates only. Select the architecture around the $50–100 target and sustainable sourcing together; do not freeze a scarce part merely because it was mentioned first.

## Exciter

- Standalone programmable DDS transmitter, initially covering 0.5–30 MHz.
- Upload an agreed binary phase sequence, mapping chips to 0° and 180°.
- Configure chip duration independently of sequence length: default 30 µs, range 10–1000 µs. Duration resolution and maximum sequence length remain to be selected.
- Store explicit sequences and programs in nonvolatile memory with integrity checking.
- Frequency table supports up to 1000 entries in user-defined order. Each entry should identify frequency, dwell, code, level, and optional digital output state.
- Support periodic sweeps, one-shot sweeps, and single-frequency operation.
- Typical program: 2 s per frequency, repeated every 5 minutes. Reject a program whose sweep and guard intervals exceed its repeat period. At 2 s per entry, 1000 entries require at least 2000 s.
- Define UTC start epoch, code start/restart rules, hop timing, and behavior when a dwell is not an integer number of code periods.
- Configure and power the exciter by USB. A power adapter must suffice after programming; no host or internet dependency during operation.
- SMA RF output into 50 Ω. Output level and flatness are not yet fixed; approximately +10 dBm is a candidate target.

## Timing and inhibit

- Use a u-blox GNSS receiver, with PPS defining time and GNSS disciplining an external voltage-controlled 10 MHz TCXO.
- Interpret the requested lock interlock as valid GNSS timing plus qualified oscillator discipline; not ionospheric TEC estimation.
- Transmission requires fresh valid time, qualified GNSS status, present PPS, oscillator lock, valid program, and healthy hardware.
- Hardware RF mute and PA-enable interlock must default off at startup, reset, programming, and watchdog failure.
- Missing PPS, stale GNSS status, loss of lock, and PA faults inhibit transmission. No transmit holdover is requested.
- Define detection latency and reacquisition qualification before implementation. Resume at a defined schedule boundary after qualification.
- Associate GNSS time messages with the correct PPS edge; specify time scale and leap-second behavior.
- Measure and document fixed signal-path delay for receiver synchronization.

## Separate PA

- Optional separate amplifier assembly, nominal 10 W delivered into 50 Ω after output filtering across the intended band.
- Support continuous single-frequency use; cooling must not rely on intermittent sweep operation.
- SMA antenna output, with connector ratings checked against mismatch voltage and current.
- Survive open and short antenna terminals indefinitely by shutdown or foldback. Continuous delivery of 10 W into a fault is not required.
- Include forward/reflected power sensing, fast current/reflection protection, temperature sensing, and thermal shutdown.
- Include final 50 MHz low-pass filter. Additional harmonic suppression across the HF band is required; filter topology remains open.
- PA power may be separate from exciter USB power. A suitably rated USB-C PD supply is an option, not a settled requirement.

## Expansion

- Reserve low-bandwidth digital I/O and firmware capacity for health/telemetry modulation. Receiver-compatible framing must be defined before enabling it.
- Future seven-output exciter: independently coded channels with shared timing and synchronization, without integrated 10 W amplifiers.
- Future meteor-radar carrier coverage must be specified separately; the initial 30 MHz upper limit may not cover the intended installation.

## Future manufacture and validation

- Aim for a future JLCPCB prototype run, with assembly availability, stackup, footprints, and test access checked at design time.
- No PCB order or fabrication at this stage.
- Before release: verify waveform correlation against the receiver, timing, startup/inhibit behavior, output spectrum, thermal operation, and PA mismatch survival across frequency and cable phase.
