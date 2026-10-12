# What the completed calibration follow-ups show

**The first recording favors globe at every tested Z correction under both processing assumptions.**
The other preselected recording favors globe in all seven complete comparisons. Two comparisons remain unfinished,
so its full-grid background-field conclusion is withheld. No complete comparison favors the specified disc.

An IMU (inertial measurement unit) records turning and acceleration. These are survey-grade airborne recordings.
The grids reuse whole, independently selected fast/level stretches; they do not create extra flights.

## Source recordings

| File | Selected UTC interval | Duration | Median / minimum ground speed | IMU type |
|---|---|---:|---:|---:|
| `ILVIS0_applanix_57300_610_LVIS_38614965.013` | 2015-10-05T12:45:50Z–2015-10-05T12:53:08Z | 438 s | 878.06 / 859.55 km/h | 21 |
| `ILVIS0_applanix_57289_610_LVIS_38614965.013` | 2015-09-24T12:47:53Z–2015-09-24T12:55:12Z | 439 s | 793.61 / 788.77 km/h | 21 |

Both dates have the same recorded configuration family. This does not establish independent physical instruments
or verified installation continuity. The September 24 recording was preselected without model fits, but had already
appeared in the original archive analysis. This is development evidence, not unseen-data confirmation.

## Complete and incomplete fits

| Grid | Converged fits | Complete three-model nodes | Whole-grid shape |
|---|---:|---:|---|
| original | 27/27 | 9/9 | globe |
| removal | 27/27 | 9/9 | globe |
| replication | 25/27 | 7/9 | unresolved |

Original and removal grids use the same October 5 recording. The replication grid uses September 24.
Each grid fixes Z gyro gain at −2%, zero or +2%, and constant Z offset at −1, zero or +1 degree/hour.
Remaining parameters are reestimated with unchanged bounds, original integration, packet-header timing and solver.
The removal grid additionally allows the existing common upstream field-removal fraction.

| Grid / model | Completed horizontal error range (m) | Remaining parameters at limits, all saved fits |
|---|---:|---:|
| original / sphere_rotating | 0.0805–0.0928 | 0–1 |
| original / sphere_still | 28.9979–29.5504 | 12–13 |
| original / flat_still | 63.5504–64.1004 | 13–13 |
| removal / sphere_rotating | 0.0805–0.0928 | 1–2 |
| removal / sphere_still | 28.9979–29.5504 | 13–14 |
| removal / flat_still | 60.5168–61.0896 | 13–13 |
| replication / sphere_rotating | 0.0844–0.0869 | 0–0 |
| replication / sphere_still | 27.1234–27.5730 | 12–13 |
| replication / flat_still | 57.5459–57.6873 | 10–12 |

Error ranges use converged nodes only. The two locked Z coordinates are excluded from remaining-boundary counts.
The [model table](models.csv) lists completed objective ranges separately from unfinished achieved costs.
An unfinished achieved cost is an upper bound on that fit’s unknown optimum, not a completed comparison.

## Why two fits remain unfinished

Both are specified-field globe fits on September 24. They exhausted the original evaluation allowance without
solver-reported success. Both saved feasible-gradient stationarity checks nevertheless pass:

| Z gain / offset | Native sweeps | Stationarity / required threshold | Horizontal / vertical achieved error |
|---|---:|---:|---:|
| +0% / +1°/hour | 199 | 0.07780 | 0.0865 / 0.5755 m |
| +2% / +0°/hour | 199 | 0.00745 | 0.0860 / 0.5802 m |

A ratio below one passes stationarity. Neither fit has another free parameter at its bound.
These saved checks indicate a stopping-budget issue rather than a large remaining projected gradient.
They do not prove a global minimum or justify relabeling either fit as converged. Accepted-step histories
were not retained, so their objective stability over successive iterations cannot be reconstructed.
All original failures and full-grid abstentions remain unchanged; no retry allowance remains.

The [failure table](failures.csv) preserves stopping messages, gradients and weak directions.

## Processing and calibration behavior

- `sphere_rotating`: fitted removal fraction 5.55112e-17–1.3102e-09; objective change -0.000304263%–0.0031765% at matched grid nodes.
- `sphere_still`: fitted removal fraction 5.55112e-17–5.55112e-17; objective change -3.68662e-08%–2.43963e-08% at matched grid nodes.
- `flat_still`: fitted removal fraction 0.74791–0.748758; objective change -7.15434%–-7.03393% at matched grid nodes.

The preferred globe’s removal fraction stays essentially zero and its costs are nearly unchanged.
Allowing removal therefore does not explain away its advantage on this recording. A fitted near-zero fraction
does not establish the actual electronics’ processing. Nor can an arbitrary original field and its unknown
subtraction be recovered independently from these logged data.

[Boundary frequencies](boundary-frequencies.csv) separate model, processing case and boundary sign.
[Weak directions](weak-directions.csv) preserve normalized-coordinate singular-vector loadings and box-feasibility.
These local diagnostics describe calibration trade-offs, not physical uncertainty or unique factory calibration.

## Residual quality and next work

The [epoch residual audit](residuals.csv) checks every saved RMS and objective against its original epoch file,
then reports axis errors, innovation RMS and lag-one dependence for all 81 saved fits, including unfinished ones.
These are in-sample residuals. A small RMS does not calibrate GPS covariance, predictive intervals or model significance.

The next useful step is a saved-residual covariance audit: longer lags, cross-axis dependence and low-frequency
behavior under one declared reference metric. That can prepare a shared error-model alternative before any refits.
A new stopping-rule or larger-budget test would require independent qualification and a separate finite allowance.
There is no archive rerun, new synthetic campaign or threshold promotion in this audit.

The specified-field/zero-field comparison is reported only after complete globe-favoring shape comparisons.
It does not identify the background field’s physical cause or distinguish solar from sidereal rate.
Group1 fused navigation supplies no independent inertial evidence. This audit performs **zero fits and zero native predictions**.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-z-followup-audit-20261012/build_report.py
```
