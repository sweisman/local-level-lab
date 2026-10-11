# What still needs validation?

Local Level Lab has two distinct projects. The primary project analyzes NASA airborne
survey recordings. The secondary project asks whether stationary consumer IMUs recover
a geographically consistent horizontal rotation field. An **IMU (inertial measurement unit)**
measures turning and acceleration. Each project needs its own error model and validation.

## NASA analysis

The completed archive comparisons and current numerical checks are described in the
[findings](ilvis0-highspeed-segments-20261008/FINDINGS.md) and
[analysis roadmap](ANALYSIS_ROADMAP.md). Outstanding work includes solver qualification,
calibration-boundary sensitivity, absolute model adequacy, timing/coordinate assumptions
and dependence between recordings. These results do not certify consumer devices.

## Stationary crowdsourcing

The app now collects still A/B blocks, original Bluetooth measurements, device information
and participant-entered location/alignment. The preliminary analyzer fits a signed reversal
rate without using latitude or an expected Earth rate. It does not call a recording a
detection. Read the [stationary method](STATIONARY.md).

Before scientific pooling:

- Demonstrate preservation of independently imposed slow rotations and establish the
  practical digital resolution, warm-up behavior and repeatability of actual units.
- Freeze level, gap, duration and alignment rules from controls, independent of the
  measured rate and expected latitude curve. Preserve failed and null recordings.
- Measure nonlinear drift, temperature effects and temporal correlation. Calibrate
  uncertainty using controls and genuinely separate recordings, rather than treating
  every sample or block as independent.
- Test reversal errors and tilt, alternative starting orientations and known-null
  apparatus controls. Check whether errors repeat with instrument, support or operator.
- Seal per-recording estimates before comparing them with location. Fit the geographic
  amplitude freely and compare alternatives; do not calibrate to the expected answer.
- Replicate across physical instruments, days and sites. Preserve those groups when
  pooling. Two devices of one model are useful replication, not a guarantee of independence.

The initial 30-minute blocks are an adjustable development setting, not an established
minimum. An overnight record is useful only if its error behavior is understood.
This experiment does not target precise vertical rate, solar-versus-sidereal differences,
polar wobble or small altitude effects.

## Earlier aircraft development

Passenger-flight simulations and route searches remain preserved as historical work.
They tested a different experiment. Their thresholds, usability domain and calibration
certificates cannot be transferred to stationary recordings or NASA data.

The former public guide is retained in [the aircraft validation history](VALIDATION_AIRCRAFT_HISTORY.md);
the [technical validation record](VALIDATION_TECHNICAL.md) retains detailed results.
No historical campaign is rerun by this change.
