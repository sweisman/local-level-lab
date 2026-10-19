# What each measurement contributes

All **53 selected stretches favor globe** in the complete full-position
comparison. This investigation asks which observations create that separation
and how the result changes when constraints are removed.

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. Recorded gyro increments drive reconstructed
orientation; that orientation turns measured acceleration into a predicted
trajectory. Receiver positions constrain the fit. The score does not directly
reward an expected Earth-rate gyro value.

[Measurement dependencies](SOURCE_AUDIT.md) · [Main findings](../CURRENT_STATUS.md) ·
[Next analyses](../NEXT_STEPS.md).

## Completed checks

| Check | Result | What it establishes |
|---|---|---|
| [Coordinate-subset scoring](../ilvis0-receiver-projection-20261018/README.md) | All 36 horizontal-only processing-case comparisons favor globe on eighteen stretches. Height-only scoring gives 28 globe and eight flat rankings. | Sensitivity at existing fitted parameters; no model was refitted. |
| [First horizontal-only refits](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md) | The 9.75-minute IMU8 stretch passes all six repeats and favors globe; the 4.07-minute IMU21 stretch passes three of six and remains unresolved. | One complete horizontal-score comparison and one incomplete sensitivity result. |
| [Timing and calibration diagnosis](../ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md) | Fixed-point and derivative checks find coupled timing/calibration freedom and different local solutions. | Explains the repeat disagreement without changing failed labels or performing a new fit. |
| [Matched timing search](../ilvis0-horizontal-multistart-20261019/INTERPRETATION.md) | Both controls and 37/38 individual fits pass, but only 2/6 selected repeat comparisons pass. | The specified-field globe solution repeats; the zero-field and flat results do not. The IMU21 sensitivity result stays unresolved. |
| [Channel-removal controls](CHANNEL_CONTROLS.md) | All 25 software checks pass. | Defines missing orientation/force constraints and an acceleration-only diagnostic; not yet a qualified recorded-data comparison. |

The timing search used 2,376 native evaluations in 6.59 hours. It is complete;
wider searches are deferred. [Every attempt](../ilvis0-horizontal-multistart-20261019/DETAILS.md)
and the [calibration CSV](../ilvis0-horizontal-multistart-20261019/attempts.csv)
preserve the full outcome, including failures.

## What removing height exposed

The horizontal score advantage persists. In the complete IMU8 comparison,
horizontal RMS is about 0.37 m for specified-field globe, 7.6 m for zero-field
globe, and 17–34 m for flat depending on processing case. Those are in-sample
scores, not independent prediction accuracy.

However, removing height from the score permits implausible vertical paths.
Across the first refits, unscored height RMS ranges from about 0.65 to 114 km.
Even the latest repeatable specified-field IMU21 solutions miss height by about
646 m. These are reconstruction errors, not measured aircraft altitude changes.

Heights still enter initialization, covariance and propagation. Both inertial
channels and conventional receiver coordinates remain. This is sensitivity to
the scored height constraint, not a valid full-flight reconstruction, an
altitude-independent test or isolated gyro evidence.

**An unresolved sensitivity result does not reopen the completed main
comparison.** It identifies limits on what stronger interpretations the present
model comparison can support. It supplies no positive flat-Earth finding.

## Next: separate the sensor channels

The [channel-control plan](CHANNEL_CONTROLS.md) makes the replacement assumptions
explicit. Acceleration alone leaves an orientation angle unconstrained. Removing
acceleration instead requires a stated force history and independent treatment
of initial tilt. Fused navigation cannot supply the missing measurement.

The first diagnostic compares measured acceleration magnitude with the magnitude
required by each receiver-trajectory model, without assuming an attitude. It
still depends on gravity, receiver coordinates and calibration. Independent
generated-motion checks and trajectory-derivative uncertainty must be qualified
before applying it to recordings.

After that qualification, a finite matched recorded-data comparison can be
prepared. Held-out prediction, correlated errors and shared-flight dependence
remain subsequent checks; finite searches do not establish global optima or
calibrated statistical significance.

The [saved-artifact inventory](../ilvis0-contribution-inventory-20261018/COVERAGE.md)
records eighteen complete reusable six-fit sets and all missing references.
The [initial development scope](PLAN.md) and [detailed study history](../STUDY_HISTORY.md)
preserve the earlier stages.
