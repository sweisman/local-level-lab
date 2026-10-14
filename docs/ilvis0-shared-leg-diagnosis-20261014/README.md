# Same flight leg, different recorder completion

The completed recovery reports **30 globe preferences, zero flat and 23 unresolved**.
The receiver-track inventory contains twelve overlapping recorder pairs; **6**
have different current completion outcomes. These are candidate shared tracks, not
verified aircraft or installation identities. The three priority pairs each have
one unresolved recorder blocked by exactly one primary fit.

This audit reads sealed fits, saved tangents, prediction errors and the existing
matched-time rate summaries. It performs **zero new fits, zero native predictions
and zero original-file reads**. It does not change any result label.

## What the two recorders measured

An inertial measurement unit (IMU) measures turning and acceleration. The following
differences use summed original angular increments, converted to aircraft-mounted
axes, on the **same complete UTC seconds**. Signs are left recorder minus right;
the linked CSV identifies both filenames and exact overlapping bounds. These are
rates including aircraft motion, not inferred background fields or bias estimates.

| Date | IMU types, left / right | Matched seconds | Mean X, Y, Z difference (°/h) | RMS X, Y, Z difference (°/h) | Current result, left / right |
|---|---|---:|---|---|---|
| 2009-10-24 | 8 / 21 | 659 | +0.119, -0.520, -0.121 | 8.418, 13.107, 11.469 | unresolved / globe |
| 2015-09-26 | 21 / 21 | 505 | +0.003, +0.110, +0.050 | 3.683, 5.748, 2.153 | unresolved / globe |
| 2015-10-07 | 21 / 21 | 519 | -0.003, +0.228, +0.198 | 12.116, 24.126, 3.404 | unresolved / globe |

The mean differences alone do not establish whether noise, mount alignment,
calibration or processing caused the solver difference. RMS differences preserve
time variation that an overall mean can hide. Mount conventions are applied
separately; matching a route does not establish identical lever arms or clocks.
The fuller course-frame correction uses fused Group-1 attitude and remains a
consistency diagnostic, never independent Earth-model evidence. The
[analytics definitions](../ilvis0-position-stability-trial-20261013/ANALYTICS.md)
explain the raw, level-course proxy and fused-context columns.

## The exact checks that failed

The endpoint and fresh gradient limits are 1e-4; relative-cost change must be at
most 1e-8; actual predicted-position movement must be at most 1 mm RMS per axis
and 1 cm at every receiver epoch. A ratio below one passes that check. These are
numerical tolerances, not instrument accuracy specifications.

| Date / unfinished stretch | Model / processing | Endpoint gradient / limit | Fresh cost change / limit | Largest axis RMS change (mm) | Failed checks |
|---|---|---:|---:|---:|---|
| 2009-10-24 / 3df34ea3 | sphere_rotating / unsubtracted | 0.0713 | 1.07 | 0.02625 | relative_cost |
| 2015-10-07 / a953c8dd | sphere_rotating / profiled_removal | 0.00824 | 4.01 | 0.001773 | relative_cost |
| 2015-09-26 / e6629f14 | flat_still / profiled_removal | 0.0992 | 0.0296 | 3.766 | position_rms_down |

All three already pass endpoint and fresh gradient checks. The October 2009 and
October 2015 background-field fits fail **only the relative-cost change check**;
their correction moves predicted positions by micrometres. The September 2015 disc
fit passes the cost check but moves vertical predictions by about 3.77 mm RMS,
exceeding the unchanged 1 mm limit. None ran out of its fit allowance.

The flat fit's stopping failure is not a flat preference. Its saved cost is much
larger than the globe-family cost on that recorder. Conversely, small movements
do not justify silently accepting the other two failures. Saved rejected steps
cannot establish the prediction noise floor or rule out nonlinear curvature.
The [priority fit CSV](priority-fits.csv) records objective values, bounds, local
conditioning and the weakest parameter combinations alongside these checks.

## What repeated starts show

These are primary-versus-repeat predictions from the **same recorder and interval**,
not cross-instrument comparisons. Agreement limits remain 1e-6 relative cost and
1 cm RMS on every axis; both starts must pass their own stopping checks as well.

| Stretch / repeated model | Primary / repeat passed | Relative cost difference | Largest axis prediction difference (mm) |
|---|---|---:|---:|
| 233183f6 / sphere_rotating | True / True | 3.31e-09 | 0.001361 |
| 3df34ea3 / sphere_rotating | False / True | 1.91e-10 | 0.03812 |
| a953c8dd / sphere_rotating | False / False | 9.76e-09 | 0.0002403 |
| e6629f14 / sphere_still | True / True | 1.07e-09 | 0.4461 |

The October 2009 repeat passes while its primary does not. Approximate agreement
does not replace the failed primary. The October 2015 primary and repeat both
remain unresolved; the September repeat checks the zero-field globe, not its
unfinished disc fit. These different checks must not be conflated.

## Next bounded investigation

1. Measure fresh prediction and tangent agreement at the three failed endpoints
   and their corresponding successful-recorder endpoints. Preserve each original
   full stretch and compare the raw measurements on the common UTC interval.
2. Test deterministic repeat evaluation, value-versus-tangent prediction consistency,
   and full/half/quarter local corrections under the original bounds and clock.
   A physically small correction can still change a stringent whitened cost check.
3. Diagnose the vertical direction separately for the September disc failure.
   Changing the cost tolerance cannot resolve its position-stability failure.
4. Qualify any numerical change on known-answer controls and a separately frozen
   paired trial with all three models and both processing assumptions. Do not
   substitute a successful neighboring recorder or promote saved endpoints.

No broader rerun or additional nuisance freedom follows from this audit. The
completed recovery allowance remains closed. Background-field cause, absolute-fit
adequacy and statistical uncertainty remain separate questions.

## Reproduce

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py -- ~/venv/bin/python docs/ilvis0-shared-leg-diagnosis-20261014/build_report.py
```

[All twelve recorder pairs](pairs.csv), [all new and reused stopping endpoints](stopping-gates.csv),
and [priority fit details](priority-fits.csv) retain the numerical evidence. The
receipt hashes every inspected input and records the numerical environment.
