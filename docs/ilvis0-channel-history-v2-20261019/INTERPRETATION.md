# What survives when gyro observations are omitted?

**This acceleration-magnitude constraint excludes none of the candidates.**
All 27,468 group cases overlap under the declared assumptions. A single zero
gain/offset correction remains unexcluded in every assessed group for all
24 recording/clock/receiver-error/candidate histories. No per-window calibration
adjustment was needed for that necessary-constraint result.

An **IMU (inertial measurement unit)** records turning with gyroscopes and
specific force with accelerometers. This test uses only the latter and receiver
positions. It does not replace the omitted turning observations with fused
attitude, assumed heading or an expected rotation field measured by the gyro.

## Same recordings, broad history coverage

| Recording configuration | Original selected stretch | Assessed packet groups | Nominal assessed duration | Saved complete-observation preference |
|---|---:|---:|---:|---|
| Ames 510 / IMU8 | 585.04 s | 552 | 552 s — 94.4% | Globe |
| LVIS 610 / IMU21 | 244.00 s | 211 | 211 s — 86.5% | Globe |

Every group contains the same 200 original packets under both clock hypotheses.
Header elapsed durations total 552.0355 and 211.0002 seconds respectively.
The discarded edges lack the required ±16-second receiver stencil; outside-
interval and partial-tail groups remain listed in the [inventory](groups.csv).
The counts describe adjacent groups, not independent observations or flights.

The two recordings retain their previously selected north/south and IMU8/IMU21
coverage. Their conservative provenance groups are recorded in the manifest;
physical installation identity is not inferred from configuration bytes.
This is retrospective development, not untouched confirmation.

## What this adds to the snapshot study

The earlier check examined only three short windows per recording and relaxed
the shared-calibration dependence. This continuation covers the supported
history, keeps the same packets under both clocks and tests one unchanged
calibration point across all groups. Receiver estimates have a bounded central-
to-continuous-average correction; they are not silently treated as exact packet
averages. No scientific measurement is interpolated.

The declared error envelopes are intentionally conservative. They retain
receiver-coordinate error and polynomial truncation, gravity, count resolution,
clock offset, force averaging and calibration alternatives. They are sensitivity
assumptions, not measured per-unit specifications or calibrated confidence limits.

## What it does not establish

The common zero-calibration point passes these **relaxed scalar constraints**.
Shared receiver perturbations, gravity and latency are not jointly solved.
Thus this is neither a full feasible gyro-free trajectory nor proof that all
three physical models explain the entire measurement record equally well.
It supplies no percentage of evidence attributable to gyroscopes.

The complete gyro-driven reconstruction favors globe on both recordings and
across all 53 selected stretches. This reduced constraint does not reproduce
that discrimination. Predictive testing and measurement uncertainty remain
necessary for a stronger attribution of the full method's separation.

## Verification and next stage

All 3,052 calculation identities passed, with no missing or unsupported group
cases. The study used 3,052 receiver operators and 9,156 force boxes in 185 seconds;
it used no new fits, native integrations or original-file reads. Twenty-two
focused controls qualify the new group/averaging/worker paths. The unlaunched
earlier preparation and every frozen source/input remain preserved.

The contribution diagnostic can now move to prediction and covariance work,
rather than another search for scalar separation under narrower chosen bounds.
The earlier matched prediction study completed 10/12 fits and retained an
unresolved aggregate result; its local uncertainty excluded bounded calibration
and covariance-estimation uncertainty. That is the next methodological gap.

[Results](README.md) · [Every scalar case](envelopes.csv) ·
[Common-zero checks](shared-zero.csv) · [Frozen method](PLAN.md) ·
[Earlier prediction study](../ilvis0-prediction-covariance-20261012/RESULTS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
