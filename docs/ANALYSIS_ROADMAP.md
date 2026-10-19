# Analysis roadmap

## Starting point

<!-- current-status:start -->
**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.
See the [verified current status](CURRENT_STATUS.md) for coverage, background-field comparisons and the supporting result records. All selected comparisons have passed their required numerical checks.
<!-- current-status:end -->

The main full-position comparison and its numerical recovery are complete.
The same 53 preselected stretches total 424.3 minutes; each is counted once.
All also prefer the specified background field over zero under both processing
assumptions. These are numerical model preferences, not a calibrated significance
level or a count of independent flights.

An **IMU (inertial measurement unit)** records angular motion and specific force.
Gyroscopes supply the central turning observations. Accelerometers and
primary-receiver positions constrain the reconstructed trajectory. Fused
navigation is used for motion screening and decoder checks, not independent
model evidence.

## Current execution order

1. Qualify bounded nonlinear calibration for the channel comparison. The
   [72-case local matrix](ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md)
   retains changing-motion differences but has infeasible wrong-model linear
   corrections. A constant gain already erases scalar straight-leg separation
   in the [known-answer control](ilvis0-measurement-contribution/CALIBRATION.md).
   Qualify quantization and synchronization and define a common motion-based
   support policy. Exact-force and
   derivative controls pass; the completed error-budget matrix now preserves
   approximation/averaging successes and failures separately.
2. Freeze a finite matched recorded-data study only after those controls pass.
3. Establish prediction on unused observations and an adequate shared residual
   model; then assess confidence and independent replication.
4. Develop a freely estimated background field and, where supported by precision,
   test solar versus sidereal rate.

The [height-removal sensitivity work](ilvis0-measurement-contribution/README.md)
is complete. One of two stretches passed all repeat checks. The other remained
unresolved after a 38-start matched timing search, despite 37 individual passes
and passing controls. Removing height also allowed implausible vertical paths.
Further timing-grid expansion is deferred; this sensitivity outcome does not
reopen the original full-position comparisons.

The first [channel-removal controls](ilvis0-measurement-contribution/CHANNEL_CONTROLS.md)
pass 25 software checks. They establish geometric requirements, not a qualified
recorded-data likelihood.

## Recovery development history

The [detailed study history](STUDY_HISTORY.md) and
[earlier technical roadmap](ANALYSIS_HISTORY.md) preserve the progression from
twelve completed comparisons to all 53. Failed fits, interrupted work and
superseded methods remain part of that record. Historical counts apply only to
their own stage.

## Priority and scope

| Priority | Work | Completion requirement |
|---|---|---|
| Current | Separate measurement contributions | Explicit missing-channel constraints, independent physical controls and a matched finite recorded-data comparison. |
| Next | Predictive adequacy and correlated errors | Nuisance fitting on training data only, withheld predictions and checked uncertainty. |
| Next | Independent-flight accounting | Provenance-supported flight/instrument groups and overlapping-time accounting. |
| Follow-on | Free rotation field and rate | Identifiable field parameters with calibration, timing and unknown processing considered jointly. |
| Supporting | Exact device documentation | Better-supported assumptions where available; it does not suspend modeling. |

No new corpus expansion, synthetic campaign or production threshold follows
automatically from a software check. New numerical studies have their own
finite freezes and retain every charged failure.

## 1. Qualify numerical completion

The main recovery is finished. New diagnostic objectives still need their own
qualification: solving the full-position problem does not qualify a score that
omits height or removes a sensor channel.

Known-answer controls must cover all declared physical models, independent
starts, active calibration bounds, weak directions, both processing assumptions
where relevant, and incorrect-model outcomes. Check objective agreement and
predicted observations, not completion counts alone. Do not require an
uninformative control to discriminate models.

Keep the full nuisance layout and unchanged numerical gates. A failed method
remains failed even when another method later succeeds. No global-optimum
certificate is claimed by finite searches.

## 2. Explain calibration-boundary saturation

The original audit found frequent parameters at their limits. Completed
[calibration profiles](ilvis0-z-profile-audit-20261011/README.md) and
[follow-up comparisons](ilvis0-z-followup-audit-20261012/README.md) provide
sensitivity evidence, but do not uniquely identify each instrument's calibration.

Future alternatives must use physically defensible, matched bounds and record
joint gain/bias/clock behavior. A larger bias allowance is not a measured drift
specification. Additional flexibility must not be introduced simply to improve
one candidate's residuals.

## 3. Assess absolute model adequacy

A lower cost does not establish an adequate observation model. Examine physical
position errors, temporal correlation, cross-axis covariance and residual
dependence on motion, speed, latitude and supported environmental measurements.

The [residual covariance audit](ilvis0-residual-covariance-20261012/README.md)
documents correlation. The [training/prediction trial](ilvis0-prediction-covariance-20261012/RESULTS.md)
remains an incomplete development comparison, not calibrated coverage.

Fit calibration and any selected covariance parameters on training observations
only. Reserve separate time blocks or supported independent flights for prediction.
Training residuals and fixed-parameter sections of a fitted stretch are not
held-out tests. Include nuisance and covariance-estimation uncertainty before
claiming calibrated confidence or absolute-fit acceptance.

## 4. Compare timing and receiver-coordinate assumptions

The [matched clock trial](ilvis0-clock-trial-20261010/README.md) preserved
globe/field preferences after reoptimization. It did not by itself establish
which physical integration period the archived increments represent. Packet
timestamps and increment intervals need not be interchangeable.

Receiver coordinates come from the primary-receiver stream rather than the
fused INS solution, but still use geodetic conventions. The
[measurement-contribution work](ilvis0-measurement-contribution/README.md)
separates these dependencies explicitly:

- Coordinate-subset scores use the retained coordinates' marginal covariance.
- Dropping height from the score does not remove its initialization or
  propagation influence; unscored errors must still be reported.
- A gyro-free comparison cannot borrow fused attitude. The new force-magnitude
  diagnostic avoids an assumed attitude but retains metric, gravity and
  acceleration-calibration dependencies.
- Receiver-trajectory derivatives need a declared smoothing/differentiation rule
  and propagated uncertainty before becoming force constraints.
- An acceleration-free comparison needs independently justified replacement
  constraints and cannot retain acceleration-derived initial tilt.

Channel interactions need not admit a single percentage of evidence attributed
to gyroscopes. Report what each matched comparison can and cannot distinguish.

## 5. Account for completion selection and dependence

Main numerical recovery removed the original incomplete-fit subset, but does
not make 53 stretches independent. Group simultaneous recorders, overlapping
time, repeated stretches and demonstrably shared physical installations.

Configuration bytes or similar filenames do not alone establish instrument
identity. Share calibration only where continuity is supported. Assess how
results transfer to independent recordings instead of counting repeated fits
as confirmations.

## Rotation-field follow-on and publication

The [rotation-field plan](ROTATION_FIELD.md) estimates the retained vector
before interpreting its cause. Audit the actual latitude, heading and
installation coverage before fitting common field parameters against gyro
offsets and unknown upstream removal.

The current specified-field versus zero-field comparison fixes its rate; it
does not measure solar versus sidereal timing. The dedicated precision stage
compares freely fitted magnitude with 15.0000 and approximately 15.0411
degrees/hour only after clock, gain, offset and shared-error uncertainty permit it.

A stronger empirical result needs adequate predictions, justified uncertainty
and replication. The existing numerical preferences remain worth reporting
with those open checks stated specifically.

## Secondary branch: stationary consumer crowdsourcing

The [stationary experiment](STATIONARY.md) uses solid supports and same-face
180° reversals. It estimates signed rate without an expected rate or latitude
in the per-session calculation. Consumer sensitivity and population inference
still need validation; the current diagnostic always abstains from a scientific
decision.

[Current findings](CURRENT_STATUS.md) · [Study index](STUDIES.md) ·
[Diagnostic requirements](ILVIS0_DIAGNOSTIC_PLAN.md).
