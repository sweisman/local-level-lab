# Horizontal-only recorded-flight development study

## Question and selection

Does the globe preference survive when the models are refitted using horizontal
receiver positions, with receiver height removed from the scored objective?

Use the shortest stretch with all six reusable primary artifacts for each of
IMU8 and IMU21. Choose by duration, filename, start time and segment ID, in that
order, from the completed artifact inventory and original frozen selection.
Neither full-position nor projected model costs enter selection. This gives
two complete stretches of about 585 and 244 seconds on distinct dates.

Fit the complete saved intervals. Do not recalculate eligibility, shorten the
intervals or select additional stretches after inspecting these results.

## Matched physical assumptions

Retain all raw angle/velocity increments, the nominal 200 Hz integration clock,
receiver epochs, initialization and h1_v3_tau60 covariance assumptions of the
existing study. Marginalize receiver covariance before whitening; score only
latitude and longitude. Keep all 26/27 nuisance columns, original bounds and
both fixed-zero/profiled upstream-removal cases. Constant gyro offsets remain
bounded at ±1 degree/hour, an assumption rather than a measured unit limit.

Use the newly qualified ridge-probe candidate and extended tangent arithmetic.
Its displacement penalty changes only the probe, never the physical-model
score. Final stationarity, cost and physical-prediction limits remain unchanged.

Receiver heights remain in initialization, covariance construction and trajectory
propagation. Both gyro and acceleration measurements remain. This is a
horizontal-objective sensitivity study, not altitude or datum independence and
not a gyro-only test. Group1 fused attitude/rates are not fitting observations.
The existing full-position fits are historical references, not matched reruns
under this new numerical method. No percentage of evidence is assigned to a channel.

## Fixed identities and allowance

Two stretches × three models × two processing cases × two starts = **24 starts**.
The primary starts at the exact current saved full-position parameter vector;
its repeat starts from the original receiver/IMU initialization rule, independently
of fitted Earth-model residuals. The same initialization code applies to each model.

- At most **200 tangent evaluations per start**, including fresh final checks,
  plus two full-coordinate diagnostic predictions: **4,848 calls**.
- Before any fitting, one full tangent at each of twelve saved primary points
  checks reconstruction: **twelve additional calls**.
- Total ceiling: **4,860 native calls**, **four total numerical threads**,
  **eight hours** including extraction/builds, no retries or expansion.
- Stop before all optimizer starts if source/extraction, parameter order or
  baseline-reproduction checks fail. Charges are never reset after interruption.
- Original files are preserved. Container and decoded-source hashes, exact
  intervals, source/environment versions and software qualification are frozen.

All baseline systems must reproduce full costs and residuals to 1e-6 relative
scale and Jacobians to 1e-5, with a unit floor in norm comparisons. The tolerances
allow the documented ordinary/extended arithmetic difference; report actual
differences rather than calling them bit-identical.

## Acceptance and reporting

Every model/case primary and independent repeat must pass the unchanged fresh
local gate. Require paired cost agreement within 1e-8 relative to max(costs,1),
axis prediction RMS within 1 mm and epoch maximum within 1 cm. These are numerical
limits, not sensor precision or calibrated scientific uncertainty.

Compare globe family against stationary flat disc first, consistently across
both processing cases. Report the field comparison only after completed shape
comparisons favor globe. An unfinished fit or failed repeat withholds the matched
comparison; preserve its costs and failure. Keep the existing 53-stretch tally.

Save the full returned parameter points, projected residuals/Jacobians, actual
receiver times, coordinates, unscored height errors, per-axis residual summaries,
start/call journals and source hashes. No production promotion or significance
claim follows. Publication verifies saved artifacts and never triggers refitting.

## Implementation and checks

- `analysis/lll/ilvis0_horizontal_observed.py`: deterministic selection, finite
  identities, input-reproduction checks and repeat acceptance.
- `analysis/tests/test_ilvis0_horizontal_observed.py`: selection independent of
  scores, incomplete/mismatched artifacts, exact budgets and failed gates.
- `analysis/tests/ilvis0_horizontal_observed_worker.py`: freeze, extraction,
  preflight, finite fits, durable accounting, automatic publication and status.
- Update the study index, next steps and status registry after preparation.

Implement and verify the metadata helpers first, then the worker. Launch only
after the passed software completion and all frozen inputs have been verified.
Preserve all earlier completed studies; no unused allowance is transferable.
