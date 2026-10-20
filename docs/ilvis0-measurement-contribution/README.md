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

The [authoritative backlog](../ANALYSIS_ROADMAP.md) orders remaining work:
nonlinear calibration and measurement error qualification, finite recorded-data
contribution checks, withheld prediction, then protected ESA replication.
The [provenance ledger](../analysis-provenance/README.md) defines conservative
split groups before new validation selection. Earlier development plans and
completed studies do not provide additional execution allowances.

## Completed checks

| Check | Result | What it establishes |
|---|---|---|
| [Coordinate-subset scoring](../ilvis0-receiver-projection-20261018/README.md) | All 36 horizontal-only processing-case comparisons favor globe on eighteen stretches. Height-only scoring gives 28 globe and eight flat rankings. | Sensitivity at existing fitted parameters; no model was refitted. |
| [First horizontal-only refits](../ilvis0-horizontal-repeat-audit-20261019/INTERPRETATION.md) | The 9.75-minute IMU8 stretch passes all six repeats and favors globe; the 4.07-minute IMU21 stretch passes three of six and remains unresolved. | One complete horizontal-score comparison and one incomplete sensitivity result. |
| [Timing and calibration diagnosis](../ilvis0-horizontal-timing-path-20261019/DIAGNOSIS.md) | Fixed-point and derivative checks find coupled timing/calibration freedom and different local solutions. | Explains the repeat disagreement without changing failed labels or performing a new fit. |
| [Matched timing search](../ilvis0-horizontal-multistart-20261019/INTERPRETATION.md) | Both controls and 37/38 individual fits pass, but only 2/6 selected repeat comparisons pass. | The specified-field globe solution repeats; the zero-field and flat results do not. The IMU21 sensitivity result stays unresolved. |
| [Channel-removal controls](CHANNEL_CONTROLS.md) | All 25 software checks pass. | Defines missing orientation/force constraints and an acceleration-only diagnostic; not yet a qualified recorded-data comparison. |
| [Independent trajectory-force matrix](../ilvis0-channel-trajectory-controls-20261019/INTERPRETATION.md) | All 18 controls pass under independent Cartesian reference motion. | Qualifies exact-trajectory force calculations; some generated cases separate without gyro input. |
| [Receiver derivatives and covariance](../ilvis0-channel-trajectory-controls-20261019/DERIVATIVES.md) | All 22 mathematical checks pass. | Preserves joint uncertainty, overlapping-window dependence and covariance symmetry; approximation is assessed separately below. |
| [Approximation and averaging matrix](../ilvis0-channel-error-budget-20261019/INTERPRETATION.md) | All 46 implementation controls pass; 81/108 candidate/window combinations pass the declared approximation screens. | Exposes trajectory bias, nonlinear response and aggregation effects before recorded-data use. |
| [Acceleration calibration ambiguity](CALIBRATION.md) | All nine known-answer checks pass; a constant gain change of 0.066–0.307% erases wrong-model scalar differences on the constructed straight leg. | A fixed-calibration acceleration-only ranking would overstate what the diagnostic distinguishes. |
| [Local calibration and changing motion](../ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md) | All 72 controls pass, with all seven calibration columns retained. Straight-leg differences disappear; changing motion retains local differences but wrong-model linear corrections exceed bounds. | Identifies the need for bounded nonlinear calibration checks; a local projection is not a feasible nonlinear fit. |
| [Bounded nonlinear calibration](../ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md) | All 12 known-answer starts pass; 32/72 matched comparisons pass all three starts. | Near-zero weakly determined cases still exhaust the budget; observed channel fitting remains blocked. |
| [Feasible scalar calibration](../ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md) | All 12 known-answer identities and 72/72 matched comparisons pass; 147 certificates and 81 actual optimizer starts. | Qualifies the mathematical calibration control while preserving scalar ambiguity; observational error and timing gates still remain. |
| [Quantization and integration-period bounds](QUANTIZATION.md) | All 17 mathematical checks pass. | Bounds packet-mean magnitudes under declared count and timing hypotheses; neither statistical averaging nor a continuous-force upper bound is established. |
| [Within-packet force averaging](FORCE_AVERAGING.md) | All 11 additional mathematical checks pass. | A continuous upper bound can be supplied with an explicit force-direction-rate assumption; absent or unsupported assumptions leave that bound unavailable. |
| [Common time support and synchronization](TIME_SUPPORT.md) | All 34 interval and prediction-bound checks pass. | Preserves whole packets and gaps, rejects unsupported receiver coverage, and bounds scalar averaging/time shifts under a declared magnitude-rate envelope. |
| [Receiver-trajectory truncation bounds](DERIVATIVE_BOUNDS.md) | All 13 deterministic checks pass. | Propagates declared higher-derivative and coordinate-error envelopes through all nine estimated quantities, retaining cross-axis sensitivity and polynomial-reproduction defects. |
| [Nonlinear force-box propagation](FORCE_BOUNDS.md) | All 30 controls pass, including independent Cartesian truth for each candidate. | Carries coordinate-jet, gravity and field bounds through the nonlinear force calculation; overlapping boxes do not establish a complete feasible fit. |
| [Combined deterministic error budget](COMBINED_BOUNDS.md) | Fifteen calibrated-increment checks and six independent end-to-end examples pass, bringing the component chain to 126 checks. | Compares continuous magnitude envelopes on shared support; the physical hypotheses still require a frozen observational assessment. |
| [Recorded acceleration-only snapshots](../ilvis0-channel-envelopes-20261019/INTERPRETATION.md) | All 144 candidate cases overlap on six fixed snapshot windows from IMU8 and IMU21; none unsupported. | The scalar constraint excludes none under the declared bounds. It is not a matched whole-history ablation or a complete feasible gyro-free fit. |
| [Whole-history scalar constraints](../ilvis0-channel-history-v2-20261019/INTERPRETATION.md) | All 27,468 cases overlap across 763 packet groups. One fixed zero gain/offset correction survives every group for all 24 history variants. | Extends coverage and shared-calibration checks; it does not establish a jointly feasible receiver history or full gyro-free reconstruction. |

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
exact-trajectory checks now pass, as do the linear derivative/covariance checks.
The new approximation/averaging matrix quantifies failures of otherwise plausible
choices. The calibration control now shows that a small permitted gain change can
erase the straight-leg scalar distinction. The changing-geometry matrix now
retains local distinctions under all seven calibration directions, with
out-of-bounds suggested wrong-model corrections. The later certificate candidate
now qualifies all mathematical comparisons by explicitly recognizing feasible
near-zero histories. It does not establish a full gyro-free reconstruction.
Deterministic quantization and direction-cone averaging bounds pass. The latter
needs an explicit supported continuous motion envelope. Whole-packet support and
common-offset prediction bounds now pass their checks. Supported clock/motion
hypotheses are explicit in the completed two-recording snapshot assessment.
Receiver truncation now has a checked bound under declared derivative envelopes;
the helper does not establish those envelopes for recordings. Nonlinear force-box
propagation and its combination with measured-increment/calibration bounds now
pass independent software checks on the same time support. No recorded-data
likelihood or calibrated uncertainty is established by those controls. All 144
recorded snapshot cases now overlap, so this scalar check excludes none of the
candidates. The complete comparisons on both recordings still favor globe.

The supported whole-history comparison is now complete: this conservative scalar
constraint excludes none, even with a shared zero-calibration point. Its relaxed
receiver/latency/gravity dependence prevents claiming a full gyro-free fit.
Held-out prediction, correlated errors and shared-flight dependence
remain subsequent checks; finite searches do not establish global optima or
calibrated statistical significance.

The [saved-artifact inventory](../ilvis0-contribution-inventory-20261018/COVERAGE.md)
records eighteen complete reusable six-fit sets and all missing references.
The [initial development scope](PLAN.md) and [detailed study history](../STUDY_HISTORY.md)
preserve the earlier stages.
