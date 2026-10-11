# What did the integration change accomplish?

**The revised calculation completed 4/6 fits, compared with 6/6 in the original calculation. It did not release either Z-axis gyro correction from its limit.** The two unfinished zero-field globe fits used their full evaluation allowances. This change is not ready to replace the original method across the archive.

An IMU (inertial measurement unit) records turning and acceleration. These are matched fits of one survey-grade recording: `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU record type 21, 438 seconds (7.30 minutes), median ground speed 878.06 km/h and minimum 859.55 km/h. They are not separate flights or independent replications.

Both calculations use the same packet-header timing, measurements, selection, calibration limits, initialization and solver. The revised calculation accounts for turning and changing force within a recorded interval, assuming ordinary increments that were not already compensated onboard. Its software controls passed; the archive comparison did not establish that this processing assumption matches Applanix recording behavior.

## Saved fit comparison

| Processing | Model | Original / revised cost | Original / revised horizontal error (m) | Revised status | Stationarity / limit |
|---|---|---:|---:|---|---:|
| No field removal | Globe, specified field | 2.30817 / 2.30814 | 0.08055 / 0.08057 | converged | 0.0106 |
| No field removal | Globe, zero field | 10748.6 / 10757.1 | 28.99792 / 29.05807 | unresolved | 53.1 |
| No field removal | Stationary disc | 49303 / 49303 | 63.55043 / 63.55045 | converged | 3.03e-07 |
| Profiled field removal | Globe, specified field | 2.30814 / 2.30813 | 0.08056 / 0.08056 | converged | 0.0087 |
| Profiled field removal | Globe, zero field | 10748.6 / 10757.7 | 28.99792 / 29.06201 | unresolved | 56.3 |
| Profiled field removal | Stationary disc | 45775.7 / 45775.7 | 60.51683 / 60.51683 | converged | 3.84e-07 |

Cost is the sum of squared covariance-scaled receiver errors, not a statistical significance. Stationarity measures whether a feasible local parameter change can still improve the fit; values above 1 in the last column fail the saved test. Original convergence labels are preserved.

The specified-field globe retains approximately 8 cm horizontal and 70 cm vertical track errors. The disc fits also converge and remain much worse. The zero-field globe fits are unfinished, so the revised calculation has no complete three-model comparison. Large achieved cost gaps are worth investigating; unfinished costs are upper bounds on the unknown best fits and cannot complete the hierarchy.

The original completed comparison remains unchanged. Model names specify background-field predictions; neither comparison identifies the physical cause of that field or determines a solar versus sidereal rate.

## Why the two unfinished fits remain unfinished

- `bias1_unsubtracted`: 200 evaluations; saved stationarity 0.00530833, 53.08 times the permitted limit. Solver message: The maximum number of function evaluations is exceeded.
- `bias1_profiled_removal`: 200 evaluations; saved stationarity 0.00563461, 56.35 times the permitted limit. Solver message: The maximum number of function evaluations is exceeded.

This records the stopping reason, not the cause of slow optimization. The saved data do not reveal the individual failed search steps.

## What remains unknown about Z calibration

All six revised fits keep Z gain at −2%, exactly as before. The specified-field globe keeps its Z offset at +1°/hour; the other two models keep it at −1°/hour. These are assumed calibration limits, not observed time-varying sensor drift. The correction is `(logged rate − offset) / (1 + gain)`; the [coefficient table](z-corrections.csv) records that convention.

The local Jacobian singular-value ratios remain in the tens of millions. These ratios describe the saved normalized parameterization, not a physical confidence interval. Singular values alone do not show which parameters form the weak directions. Neither trial saved right singular vectors, complete gradient vectors or the optimizer step history. We therefore cannot identify a Z gain–offset valley or claim that calibration is the cause of the two unfinished fits.

[All parameter changes](parameter-changes.csv) and [fit diagnostics](fit-comparisons.csv) preserve the values used here. No calibration bounds were widened.

## Next comparison

The [joint-profile plan](PROFILE_PLAN.md) specifies a staged 3 × 3 Z-gain/offset grid, with the remaining parameters reoptimized for all three models. The first stage uses the original integration and one processing case: 27 starts, at most 5,400 native sweeps, roughly 6–7 hours at measured throughput. This plan is not a run authorization. Other clocks, processing cases and integration conventions require separate stages.

This audit used **zero native predictions and zero optimizer starts**. It verified both publication receipts, completion hashes, identical embedded reference, selection, measurement provenance, assumptions and numerical environment.

## Reproduce

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-integration-audit-20261011/build_report.py
```
