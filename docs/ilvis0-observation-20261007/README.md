# From recorded increments to an independent comparison

The six-file observation check is complete. All original hashes, strict packet checks and
dated receiver timing checks passed. The adapter produced **2,930 complete diagnostic
seconds**, of which **2,923** have nearby receiver positions and supported coordinate rates.
These are measurements prepared for investigation, not newly accepted level-flight windows.
The six files were the existing date/configuration representatives selected before gyro
checks; they were not selected to maximize an Earth-model result.

The adapter preserves native signed integer increment sums and the original packet/time
boundaries. It reports rates using both accumulated header intervals and the fixed-200-Hz
hypothesis. It excludes incomplete seconds, unknown raw status, missing installation settings,
mount changes inside a second and unsupported gaps. It keeps every excluded block and reason.
Summed angle increments are not coning-corrected net rotations. Originals remain untouched.
These one-second summaries are for diagnostics. A motion forward model must return to the
packet-level increments, preserving short aircraft corrections and accounting for finite
rotations and rotated acceleration; averaging those effects away is not a motion correction.

No fused Group-1 attitude, gyro rate or acceleration supplies the observations or the
geometry calculation. Checksummed primary-receiver coordinates provide route context. Their
coordinate conventions remain an explicit assumption, and ground track remains different
from aircraft heading. The geometry diagnostic assumes aircraft motion could be corrected
independently, then explores fixed crab, bank and pitch uncertainty. It is an assumption
test, not a measured motion correction.

## What the geometry says

An unknown constant IMU bias absorbs much of the nearly constant predicted Earth signal.
Allowing linear drift absorbs more. The 26 October 2010 route leaves the most separation
among these six. Under the idealized motion correction, after constant and linear bias
removal, its worst-envelope remaining vector RMS is:

| Comparison | Predicted separation remaining |
|---|---:|
| Rotating globe / still globe | 0.84 degrees/hour |
| Rotating globe / still disc | 2.66 degrees/hour |
| Still globe / still disc | 2.50 degrees/hour |

These numbers are predicted differences, not measured Earth signals, instrument noise
specifications, calibrated power or accepted comparisons. That file also retains its earlier
marginal gyro-scale failure. No representative was replaced because it failed a check.

A more conservative local projection also allows freely varying gain and mounting tangents.
It removes almost all of the separation. Those tangent coefficients have **no physical
amplitude bounds**: this result does not show that small, independently bounded calibration
errors could actually reproduce a whole model difference. The next design test needs
defensible gain, mount and bias bounds instead of either ignoring them or leaving them
unrestricted. Likewise, wholly unrestricted aircraft rotation can absorb every model
contrast. Raw acceleration and GPS may constrain that motion in a joint physical model;
this check has not yet constructed or validated that model.

## What remains independent, and what remains unknown

None of these six files contains Group 10002, and none has a receiver-stationary interval
at the tested resolution. The public [Applanix ICD](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
describes Group 4 as time-tagged IMU data suitable for POSPac, while Group 10002 is separately
identified as direct IMU output. The distinction makes processing provenance worth checking;
absence of Group 10002 neither proves Group 4 is corrected nor proves it is uncorrected.
The modern ICD does not establish every legacy processing detail in these recordings.

There is still no independent demonstration that Group 4 retains Earth rate unchanged.
Agreement with fused navigation cannot provide that demonstration. Instrument-specific
calibration, filtering, coning/sculling, latency and Earth-dependent corrections remain
explicit unknowns. A proprietary manual is not the sole route to resolving them, but seeing
an expected Earth-like component would not alone prove independence either.

The next constructive stage is an archival forward model: predict raw increments and GPS
motion jointly under each candidate geometry, with aircraft attitude and sensor errors as
constrained nuisance quantities. Gravity and translational acceleration must be separated;
body heading must not be equated with ground track. Compare predictions with independent
motion controls before attempting an Earth-model fit. Keep useful pairwise questions,
including globe versus disc, even if the complete three-way question remains unresolved.

## Reproducibility

Reusable code: `analysis/lll/ilvis0_observation.py`. Detached launcher:
`analysis/tests/ilvis0_observation_worker.py`. The completed local output is
`data/ilvis0-observation-20261007/`; it must not be resumed with revised source. This evidence
directory preserves the frozen manifest/source snapshots, completion, compressed complete
report, per-file inventory and compressed increment/receiver artifacts. Nine new deterministic
tests and fifteen preceding installation/motion tests passed before launch. The new tests
cover increment arithmetic, gaps, clock alternatives, mounting changes, unsupported timing,
independence from gyro values, longitude wrapping and corrupt recovery artifacts.

There were zero Earth-model fits, eligibility changes, original deletions or new campaigns.
The separately authorized exploratory fitting allowance remains unused. All 232 originals
remain stored, and all previous studies and failure reports remain frozen.
