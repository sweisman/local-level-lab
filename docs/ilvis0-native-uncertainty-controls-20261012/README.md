# Native prediction uncertainty controls

The uncertainty adapter now consumes the existing inertial measurement unit (IMU)
integration and its derivatives. Six independently constructed short geographic
paths check both hemispheres and all three physical candidates. All 27 parameter
columns, including a possible upstream rotation-removal fraction, agree with
separate central differences of the native value implementation.

| Candidate | Latitude | Known-path error (m) | Largest derivative discrepancy (m) | Training rank / parameters |
|---|---:|---:|---:|---:|
| sphere_rotating | -45° | 0.000225 | 0.000135 | 27/27 |
| sphere_rotating | +45° | 4.11e-05 | 9.98e-05 | 25/27 |
| sphere_still | -45° | 0.000225 | 0.000179 | 27/27 |
| sphere_still | +45° | 4.12e-05 | 0.000165 | 25/27 |
| flat_still | -45° | 0.000226 | 0.000184 | 27/27 |
| flat_still | +45° | 4.12e-05 | 0.000101 | 25/27 |

Derivative discrepancies are per unit of a normalized parameter. Acceptance limits
were fixed at 0.002 m for known-path error and 0.0002 m for derivative discrepancy.
The paths include receiver observations between packet boundaries and two clock
constructions. Training uses the first 16 receiver epochs; prediction uses the last
eight. Future predictions cannot change the training rank calculation.

The six-case matrix uses exactly 348 native software sweeps, with zero optimizer
starts and no NASA originals read. Failed calls remain charged; allowances are
checked before execution. Boundary parameters remain in the rank calculation.

These 12-second controls verify interfaces and derivatives. They do not validate
archive uncertainty, recover unknown processing, establish confidence coverage or
prove a scientific model. Their limited calibration rank is reported explicitly.
The adapter reports local unconstrained geometry and sampled prediction changes;
neither is a calibrated interval or a reoptimized profile.

Reproduce from the repository root:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-native-uncertainty-controls-20261012/build_report.py
```

The numerical comparison will be prepared separately before any archive fits run.
