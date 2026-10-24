# Finite observed ESA prediction pilot

## Prerequisites and fixed data

The interval preparation and all 48 matched weighted software controls have
completed and their saved evidence is verified. Use their exact common fitting
pipeline and the prepared 360,028 intervals. Do not reopen original recordings,
change the selected twenty-minute interval or inspect protected groups.

Keep 1,200 fixed query epochs: the earlier 800 train calibration; the later
400 score a continuous forecast after it is saved. The reusable raw archive,
training rows and separate scoring rows must retain their preparation hashes.
Use both working receiver-error policies and the declared linear-point sampling
hypothesis. Actual adjacent timestamps set the clock; do not replace them by
a nominal sample period or introduce a second timing search.

## Matched fits

Freeze 24 identities: three candidates × two processing cases × two working
receiver-error cases × two starts. Retain every active nuisance column and the
same calibration domain used by the qualified software controls: attitude X/Y
±0.25 rad, yaw ±π rad, velocity ±20 m/s, position ±100 m, gyro offset ±1°/h,
accelerometer offset ±0.1 m/s², gyro gain ±1%, accelerometer gain ±2%, antenna
offset ±5 m, gravity correction ±0.1 m/s² and latency ±0.01 s. These are declared
sensitivity assumptions, not measured per-unit calibration bounds.

The zero-removal case fixes upstream removal at zero. The other profiles a
common removal fraction in [0,1] for every candidate. Starts are normalized
zero and the fixed alternating −0.001/+0.001 pattern. Use the qualified
near-zero stopping composition, retaining the ordinary nonzero-cost checks.
Do not add starts, widen limits or retry a failed fit after seeing results.

Choose each model/case primary by the smallest converged training cost; retain
the declared start order for exact ties. Later positions must not influence
that choice, calibration, initial state or weights. Report both starts and their
prediction spread, without treating the spread as a confidence interval.

## Scoring and interpretation

Save each full forecast before opening the scoring artifact. Report north,
east and height errors in one common receiver-coordinate chart, using the
receiver's ellipsoidal radii and height for every candidate. Wrap longitude
differences consistently. This is a local conversion of coordinate errors to
metres, not independent GNSS geometry or an extra inertial measurement.

Report earlier and later horizontal/height RMS, maximum errors and total
three-dimensional RMS. Rank later-position agreement by total RMS as a
descriptive comparison, not a likelihood ratio or calibrated test. A full
matched comparison requires converged primaries and complete predictions for
all three candidates under the same processing and error assumptions.

Compare the better globe model with the specified disc first. Compare nonzero
and zero background fields only after the complete shape comparison favors a
globe model. Keep the existing physical screens: horizontal RMS ≤10 m, height
RMS ≤30 m, maximum horizontal error ≤50 m and maximum absolute height error
≤150 m. Apply them separately to training and prediction. A preferred model
that fails prediction accuracy is not an adequate flight reconstruction.

Neither relative agreement nor these descriptive screens establish confidence,
independent replication, the field's source or solar-versus-sidereal timing.
This pilot uses one development recording. NASA's original 53 comparisons
and the seven protected ESA confirmation groups remain unchanged.

## Allowance and execution

Allow at most 200 fitting calls including stopping checks, plus one continuous
forecast per identity: 4,824 native calls total. Before launch, compute the exact
training-prefix count from the saved times and full latency allowance. The
per-identity packet/query ceiling is
`200 × training_prefix_packets × 800 + 360028 × 1200`.
Charge every call before execution. Interrupted starts remain charged.

Use four workers with one numerical thread each and an eight-hour cooperative
ceiling. This is a finite development allowance, not a promise that every start
will converge. No retries or extra starts are allowed. Each worker reuses the
same frozen input artifacts; no full-source file is copied for individual fits.
Both working covariances have only 800 training epochs, within the explicit
1,024-epoch dense cap. Longer recordings require the structured calculation.

Before launch, freeze source/environment/input hashes, the exact prefix count,
task identities, allocation and limits, after source-bound tests of scoring,
selection, isolation and accounting pass. Save all fits, failures, forecasts,
scores, calibration bounds and journals. Verification and publication use saved
artifacts only and must not refit or propagate.

[Pilot methodology](PLAN.md) · [Working error cases](../ESA_ERROR_POLICY.md) ·
[Qualified controls](../esa-weighted-training-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
