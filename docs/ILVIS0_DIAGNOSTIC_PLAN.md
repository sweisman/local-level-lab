# Diagnostic requirements

The main comparison is numerically complete: **53 globe preferences, zero flat
preferences and zero unresolved stretches**. Further diagnostics strengthen
interpretation; they are not a remaining main-analysis recovery queue.

An **IMU (inertial measurement unit)** supplies recorded gyro and acceleration
increments. Primary-receiver observations constrain the reconstructed motion.
Group-1 fused navigation remains decoder-check and motion-context material.

[Authoritative backlog](ANALYSIS_ROADMAP.md) · [Public next steps](NEXT_STEPS.md) ·
[Current findings](CURRENT_STATUS.md).

## Foundation: provenance and confirmation boundary — F01/F02

Group source aliases, UTC overlaps, shared legs and supported flight/installation
relationships before choosing validation splits. Distinguish recorded
configuration from proven physical instrument identity. Use conservative groups;
do not equate 53 stretches with 53 independent flights.

The [metadata ledger](analysis-provenance/README.md) now records 27 conservative
groups for the 53 stretches, with eleven deterministic grouping checks. These
groups do not establish independent instruments or installations.

ESA recording 187 is development material. All other currently cataloged ESA
flight groups are protected from model fitting and outcome inspection until
the method and confirmation identities are frozen. Integrity and receiver-only
eligibility checks are allowed. Group shared files and overlaps together.

## Measurement contribution — C01–C04

Completed controls include independent Cartesian force truth, receiver
derivatives with joint covariance, approximation and averaging stresses,
constant-gain ambiguity, and the seven-column local calibration matrix.
Preserve all failed approximation screens and uninformative controls.

Remaining gates are bounded nonlinear calibration, quantization, integration
intervals/time association, averaging, common motion-based support and propagated
uncertainty. Require known-answer, boundary and independent-start checks before
a finite recorded-data comparison. Use the same physical region for all candidates.

The [nonlinear study](ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md)
passed 12 known-answer starts but only 32/72 complete matrix comparisons. It is
complete and cannot resume; observed channel fitting remains blocked. The first
[17 quantization/period checks](ilvis0-measurement-contribution/QUANTIZATION.md)
pass, without establishing a continuous-force bound or statistical coverage.

Acceleration magnitude is a gyro-free necessary constraint. Agreement neither
determines orientation nor proves a complete gyro-free fit. Never insert fused
attitude, equate aircraft heading with GPS course, or retain an omitted sensor
through initialization. Do not tighten bounds or select favorable residuals to
create discrimination.

[Channel requirements](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md) ·
[Calibration evidence](ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md).

## Withheld prediction and adequacy — V01/V02

Develop a shared correlated-error model on training observations only. Preserve
cross-axis dependence, full-record drift anchors and uncertainty from calibration
and covariance estimation. Local unconstrained covariance alone does not qualify
bounded nonlinear prediction intervals.

Freeze group membership, training/prediction blocks, initialization dependencies,
physical adequacy criteria and finite numerical limits before evaluation. Keep
prediction observations out of fitting and covariance selection. Within-record
prediction and cross-flight calibration transfer are distinct tests; transfer
requires supported installation continuity.

Report physical errors in every axis, temporal correlation and residual trends
against motion, speed and latitude. A better horizontal fit with kilometres of
height error fails to describe the full flight. A lower relative cost alone does
not establish adequacy.

The NASA corpus has already informed development. New blocked tests are
retrospective validation, not untouched confirmation. Earlier incomplete
split-recording trials retain their labels.

## Independent replication and scalability — L01/E01/E02

Implement the initial ESA eligibility proposal before examining model outcomes.
Qualify rate-versus-increment handling, clocks, axes, lever arms and dataset-specific
calibration assumptions. Reuse no Applanix bound or threshold automatically.

Before long fits, validate structured covariance, marginal-coordinate whitening
and matrix-free residual/Jacobian operations against dense small controls.
Check streaming integration and receiver association across block boundaries.
Computational blocks must not silently drop statistical dependence.

Freeze the development method and adequacy/error rules before reserved ESA
confirmation. No eligible interval, no estimable contrast or a failed fit remains
an explicit outcome; no outcome-driven policy relaxation follows.

## Gyro prediction and publication — G01/U01/U02

Keep the raw plot unchanged. Its companion compares signed variation with
course/latitude/mount/transport/field predictions. Identify fitted-orientation
dependencies and retain unknown aircraft motion or mounting. Fused attitude and
common accumulated sign cannot establish independent curvature evidence.

Assemble one versioned paper dataset with groups, observations, assumptions,
fits, withheld errors, exclusions and hashes. Calibrate the complete shape-first
hierarchy, including selection of the better globe model, the later field
comparison, correlated errors and nuisance fitting. Numerical preference,
physical adequacy, prediction and calibrated detection stay separate.

## Deferred and supporting work

Further main NASA recovery is retired. Broad horizontal timing searches,
large Z-axis grids and synthetic passenger-route optimization are deferred.
Retain completed clock/calibration evidence; the packet timestamp need not equal
an increment's physical integration period.

Free background-field estimation follows contribution and prediction gates;
solar/sidereal precision follows a freely estimated field and supported clock,
gain and offset precision. Wuhan and stationary-consumer expansion remain
separate lower-priority branches. Exact instrument documentation supports
assumptions but does not suspend qualified modeling.

[Historical diagnostics](DIAGNOSTIC_HISTORY.md) preserve earlier plans and results.
