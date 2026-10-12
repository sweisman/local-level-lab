# Matched prediction comparison: prepared scope

This is a costed development plan, not a running study. The launcher still needs
implementation and software qualification. No new archive computation is authorized.

The question is whether the model preferences and future-position errors remain
stable under two shared assumptions about slowly correlated receiver error.
The completed six-fit chronological comparison remains unchanged, including its
one unfinished flat-disc fit. This comparison will not retry that fit.

## Recording and measurements

Use the already selected October 5, 2015 recording
`ILVIS0_applanix_57300_610_LVIS_38614965.013` (IMU21):
12:45:50–12:53:08 UTC, 438 seconds. Minimum receiver ground speed is 859.55 km/h;
median is 878.06 km/h. This control has already been examined, so the new
comparison is retrospective development evidence, not independent confirmation.

The inertial measurement unit (IMU) supplies the original angle and velocity
increments. Receiver observations supply position. Group1 fused navigation is
not used as an independent observation. Preserve every selected packet and the
original conversions, installation assumptions and header-elapsed clock.

Use the first 292 of 439 receiver epochs for training, ending at 12:50:41 UTC.
The remaining 147 epochs, 12:50:42–12:53:08, test continuous prediction.
Initialize and fit calibration from training data only. Do not reset the
integrated path or refit parameters at future receiver positions.

## Matched assumptions

Run all three candidates under each processing case: no upstream removal,
or a fitted common rotation-removal fraction. Retain the ±1°/hour constant
gyro-offset bounds, ±2% gyro-gain bounds and all other existing bounds.
These are sensitivity assumptions, not measured instrument specifications.

Apply each covariance to every candidate and processing case:

| Assumed component | North / east / up standard deviations | Time behavior |
|---|---|---|
| Independent receiver floor | 0.3 / 0.3 / 0.7 m | Independent epochs |
| Correlated receiver error | 1 / 1 / 3 m | Exponential decay, either 10 or 300 seconds |
| Shared offset | 1 / 1 / 3 m | Constant through the selected stretch |
| Linear drift | 1 / 1 / 3 m | Zero at first epoch, stated deviation at last epoch |

The two correlation times bracket shorter and longer behavior exposed by the
saved residual audit. They are predeclared sensitivity cases, not estimates of
true receiver uncertainty. Do not select a different covariance for each model,
tune it to improve a preferred result, or report a calibrated significance level.
The existing 60-second baseline remains a reference, not another new fit.

Construct covariance across the full receiver timeline, then use its training
marginal. Keep drift anchored to the full stretch. Convert physical errors using
the same conventional WGS84 receiver-coordinate metric for all candidates.
Candidate dynamics retain their distinct metrics; the error weights do not
change with the model. Geodetic coordinate assumptions remain explicit.

## Numerical ceiling and output

Two covariances × two processing cases × three candidates gives **12 starts**,
one per identity, **no retries**. Each fit has at most 200 native sweeps, including
its required final convergence diagnostics: **2,400 fit sweeps maximum**.

Reserve at most 55 additional full-record diagnostic sweeps per fit: one native
tangent at the saved center, and feasible ±0.01 normalized steps along every
allowed parameter direction. Reuse the tangent's central prediction. Fixed-zero
removal has 26 parameters; profiled removal has 27. Skip an outward step that
violates a bound, record the omission and retain that parameter in rank checks.
No nuisance reoptimization is hidden in these probes.

The inclusive diagnostic reserve is **660 sweeps**, giving **3,060 total**.
Charge failed calls before execution. A failed fit retains its failure label;
diagnostics at a finite feasible saved center cannot turn it into a decision.
Use one durable worker and two numerical threads, with immutable task IDs,
exclusive locks, append-only start/sweep journals, hashed atomic outputs and
source/input/environment checks on resume. Interrupted work remains charged.

Saved runtime measurements give roughly **154–172 minutes at the ceiling**,
counting full-record diagnostics conservatively as longer tangent sweeps.
This is a planning extrapolation; the new objective has not been benchmarked.
No extraction, original-file reads, native predictions or fits occur in preparation.

Publish training and future physical position errors, correlated-error innovations,
residual dependence, calibration boundaries, full-column rank and nonlinear probe
remainders. Local Gaussian geometry and finite axis-probe ranges are diagnostics,
not calibrated prediction intervals or fully profiled uncertainty. More complete
bounded and covariance-parameter uncertainty remains separate work.

Compare globe versus the specified disc first. Discuss the specified background
field versus zero field only after complete shape comparisons favor the globe.
These candidates do not determine the field's cause or distinguish solar from
sidereal rate. Preserve abstentions and all numerical failures.

September 24 prediction replication, other recordings and a corpus rerun are
deferred, with separate predeclared scopes and allowances.

The next implementation is the tested durable launcher. Its final source and
environment freeze must be reviewable before requesting the finite compute allowance.

Reproduce this metadata-only preparation:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-prediction-covariance-preparation-20261012/build_plan.py
```
