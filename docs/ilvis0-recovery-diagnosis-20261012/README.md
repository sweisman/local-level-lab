# Recovery stopping diagnosis

The trial is complete: **15 of 24 fits passed**, including all six completed-control
fits and eight of the 15 originally unfinished primary fits. The three unresolved
stretches still lack complete comparisons. The original public findings remain
**12 globe preferences, zero flat preferences, 41 unresolved**.

This audit reads sealed results and journals only. It makes no new predictions or
fits, and changes no scientific labels. The 1,694 charged sweeps
are well below the 14,448 ceiling; the unused allowance cannot be reused.

## Why the nine failures differ

- **Four early stability failures:** the saved gradient passed, but a bounded
  linear correction did not meet the unchanged measurement-stability requirement.
- **Four early stationarity failures:** the optimizer stopped on parameter-step
  size while the independently checked gradient remained excessive.
- **One budget failure:** the perturbed disc fit remained far from stationary
  when its fitting allowance was spent.

All eight early exits used the optimizer's `xtol` parameter-step test. Small
parameter steps are therefore insufficient evidence of completion. None of the
four failed stability probes reached a fresh nonlinear correction measurement:
they were rejected by the linear prediction first. Whether those corrections
improve the actual observations is not saved and cannot be inferred here.

| Stretch prefix | Processing case | Model / role | Evaluations | Gradient / limit | Probe result |
|---|---|---|---:|---:|---|
| 03454752 | profiled_removal | flat_still / repeat | 598 | 350.8 | not_stationary |
| 03454752 | profiled_removal | sphere_rotating / primary | 32 | 1.627 | not_stationary |
| 233183f6 | profiled_removal | sphere_rotating / primary | 18 | 0.0002222 | linear_correction_not_stable |
| 233183f6 | unsubtracted | sphere_rotating / primary | 19 | 0.0001184 | linear_correction_not_stable |
| 233183f6 | unsubtracted | sphere_rotating / repeat | 29 | 3.788 | not_stationary |
| b365bdf3 | profiled_removal | flat_still / primary | 94 | 0.04737 | linear_correction_not_stable |
| b365bdf3 | profiled_removal | sphere_rotating / primary | 157 | 1.072 | not_stationary |
| b365bdf3 | profiled_removal | sphere_still / primary | 24 | 0.8403 | linear_correction_not_stable |
| b365bdf3 | unsubtracted | sphere_rotating / primary | 90 | 1.02 | not_stationary |

A gradient/limit ratio below one passes stationarity. It does not establish
measurement stability. Three of the four failed stability probes predict tiny
cost changes while predicting residual changes above the allowed limit; the
fourth predicts a larger cost improvement as well.

The failed Jacobians have a median condition ratio of
**1.13e+08**. That measures the disparity between
strong and weak local parameter combinations; it is a warning about numerical
sensitivity, not proof of its cause. Saved right singular vectors and complete
Jacobians are absent here, so the weak combinations cannot be reconstructed.
The dominant remaining gradients include gain/offset/gravity combinations and
near-boundary calibration coordinates.

One accepted fit passed three stable callbacks although its linear probe failed.
That is permitted by the frozen rule, but shows that callback stability and full
linear-correction stability are different tests. It must remain visible in the
next qualification; this audit does not change either tolerance to improve counts.

## Next numerical test

Screen a genuinely different bounded step strategy on deterministic equations
with known optima, coupled weak directions and near-boundary starts. Preserve the
same gradient, cost and measurement-stability requirements. Compare objective and
predicted observations, including failed tests. Do not select a strategy by its
preferred Earth model. An observed diagnostic must then record rejected steps,
fresh correction behavior and local tangents under a separately frozen finite
allowance. No new observed fit or all-41 rollout is authorized by this audit.

## Reproduce

Run from the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-recovery-diagnosis-20261012/build_report.py
```

The builder checks the original completion seal, manifest, summary and both
charged journals. `fits.csv` preserves every accepted and failed result; the
receipt hashes inputs, audit software and generated artifacts. Original data and
completed trial outputs remain untouched.
