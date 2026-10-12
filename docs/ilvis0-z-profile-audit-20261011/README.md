# Does Z-axis calibration explain the model separation?

**All 27 fits converged. Every fixed gain/offset combination favors globe over disc, then the specified background field over zero field.**

An IMU (inertial measurement unit) records turning and acceleration. This audit uses saved fits of one 438-second IMU21 recording,
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, with median speed 878.06 km/h and minimum 859.55 km/h.
It covers packet-header timing and the no-upstream-removal assumption. These are matched checks, not independent flights.

| Model | Horizontal error range (m) | Objective range | Remaining parameters at limits |
|---|---:|---:|---:|
| sphere_rotating | 0.0805–0.0928 | 2.30818–2.36769 | 0–1 |
| sphere_still | 28.9979–29.5504 | 10748.6–11154.4 | 12–13 |
| flat_still | 63.5504–64.1004 | 49303–50171.9 | 13–13 |

## What the grid resolves

The preferred model’s objective changes by only 2.58% across the full grid. Its excellent track fit does not require
Z gain −2% or Z offset +1°/hour: zero corrections and every other tested combination preserve the advantage.
Those two corrections were fixed, so they are excluded from the remaining-boundary counts above.
The preferred model reaches at most one other limit; the alternatives reach 12–13. Boundary counts must therefore
be interpreted separately for each model. This result removes an explanation in which the preference depends
on the two extreme Z corrections. It does not establish that the measurement model or uncertainty is fully adequate.

## What calibration remains uncertain

The best sampled preferred-model point still lies at Z gain −2%, offset +1°/hour, but its advantage over
other calibration points is small. The saved fixed-coordinate derivatives and profile costs show this direction
of improvement; they do not identify the factory calibration or instrument drift.
The weakest remaining local direction at the zero-correction point is dominated by gravity correction and
X/Y gyro gains for all three models. The [weak-direction table](weak-directions.csv) retains every loading
and its box-feasibility flags. These describe the saved normalized coordinates, not confidence intervals.
No new Jacobian was calculated. Fixed-coordinate gradients are not feasible search directions within each locked fit.

## Residuals and what follows

[Saved epoch statistics](residuals.csv) report physical errors, innovation RMS and lag-one correlation.
These are in-sample fitted residuals. They do not independently estimate GPS noise or certify a calibrated likelihood.
The next matched grid allows a common upstream background-field-removal fraction. A separately predeclared
September 24 recording then tests transfer of this robustness. Different dates do not establish independent instruments.
Both stages retain the same calibration bounds and finite grid; neither uses Group1 fused navigation as inertial evidence.

Background-field comparisons describe measured-rotation predictions, not their physical cause.
This audit adds zero optimizer starts and zero native predictions. It preserves the original 53-stretch findings.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-z-profile-audit-20261011/build_report.py
```
