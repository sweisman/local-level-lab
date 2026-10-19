# Evidence so far

The main airborne comparison is complete: **53 globe preferences, zero flat
preferences and zero unresolved stretches**, under both tested processing cases.
The same 53 preselected stretches total 424.3 minutes. The original twelve
completed comparisons and 41 later recoveries are one cohort, not separate
replications.

An **IMU (inertial measurement unit)** measures turning and specific force.
The central observation is the recorded gyroscope motion. Acceleration and
primary-receiver positions constrain the reconstructed aircraft track; fused
navigation does not supply the fitted observations.

[Verified findings](CURRENT_STATUS.md) ·
[All stretches and source tracks](ilvis0-current-findings-20261015/STRETCHES.md) ·
[Comprehensive CSV](ilvis0-current-findings-20261015/stretch-analytics.csv).

## What is established, and what is still open?

| Result or check | Present conclusion |
|---|---|
| Complete full-position model comparison | All 53 stretches pass their required numerical comparisons and favor globe. |
| Background-field comparison | All 53 also prefer the specified field over zero; its cause and freely measured rate are not determined. |
| Height-removal sensitivity | The horizontal score advantage persists, but unscored vertical paths can be implausible. One of two refitted stretches is complete; the other remains unresolved after a matched timing search. |
| Sensor-channel separation | Independent force/error controls pass and retain calibration ambiguity. The bounded nonlinear matrix qualifies only 32/72 comparisons, so observed channel fitting remains blocked. Seventeen quantization/period checks pass, without calibrated coverage or a continuous-force upper bound. |
| Prediction and significance | Earlier trials provide development evidence; calibrated significance, adequate withheld prediction and independent-replication counts remain open. |
| Shared observations | The metadata ledger forms 27 conservative split groups from 53 stretches; these are not verified independent flights or installations. |
| Independent confirmation reservation | ESA recording 187 is development material. Eight other cataloged files form seven protected groups; no ESA model comparison has been run. |

The [measurement-contribution overview](ilvis0-measurement-contribution/README.md)
explains the separate sensitivity outcomes. They do not reopen the completed
main comparisons. Unfinished calculations or nonrepeatable sensitivity fits
supply no positive flat-Earth finding.

On the original twelve completed stretches, median horizontal in-sample errors
were approximately 7 cm for specified-field globe and 47 m for flat. Those
figures describe fitting the observations used in estimation, not predictive
accuracy on unused data or an error summary of all 53.

Overlapping streams and shared flights cannot be counted as independent
replications. Model preferences describe the declared observations and physical
assumptions; a calibrated statistical significance level has not been established.
The [provenance ledger](analysis-provenance/README.md) records the grouping and
confirmation reservation. The [next analyses](NEXT_STEPS.md) prioritize sensor
contribution, withheld prediction and independent ESA confirmation before
free-field precision.

## Rotation field and additional data

Saved fits use “rotating globe” and “still globe” for specified-background-field
and zero-field predictions. These names do not identify the field's physical
cause or a cosmology. A [freely fitted field and solar/sidereal rate test](ROTATION_FIELD.md)
remain follow-on work; the current fixed-rate fit does not measure that distinction.

Longer [ESA and Wuhan recordings](external-imu-data/README.md) have been inspected
but have not entered the Earth-model comparison. They need separate selection
and observation-model qualification.

## Stationary consumer experiment

The Android app guides stationary A/B reversals on a solid surface. Its
preliminary analyzer estimates a signed horizontal reversal signal without
latitude or an expected amplitude. Consumer sensitivity, physical slow-rate
controls and uncertainty still need validation. The diagnostic always abstains
from a scientific decision; population pooling is not validated.

See the [stationary method](STATIONARY.md), [instrument checks](BENCH.md) and
[validation plan](VALIDATION.md).

## Historical development

The [detailed study history](STUDY_HISTORY.md), [technical simulation evidence](EVIDENCE_TECHNICAL.md)
and [aircraft validation history](VALIDATION_TECHNICAL.md) preserve earlier
methods, intermediate counts and failed trials. They do not provide thresholds
for the archival analysis or the new stationary protocol.
