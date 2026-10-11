# Independent geographic fitter controls

**24/24 controls passed the predefined numerical checks.** These are synthetic
software controls, not additional NASA findings. They exercise the native geographic
predictor, its automatic derivatives, receiver timing and both nonlinear solvers.
There were zero observed-data fit starts. The failed observed stopping-rule trial
and the 53-stretch first-pass findings remain unchanged.

An **IMU (inertial measurement unit)** measures turning and acceleration. Here its
three-axis increments come from independently specified continuous motion, not the
production predictor. The receiver's positions are separately generated at known
times. The fitter must reconstruct those observations while estimating calibration,
initialization and latency. See the [predefined plan](PLAN.md).

## What was tested

The six physical fixtures cover rotating globe, still globe and stationary disc,
each with a known 12-second equatorial eastward track at 220 m/s and 1,000 m altitude.
Body pitch and yaw vary smoothly. Eight-point Gaussian quadrature integrates the
analytic body angular rate and specific force. Receiver positions follow the appropriate
analytic coordinate metric; neither navigation kernel generates the input data.
Receiver epochs fall between packets, with independently specified latency.

Each model has constant-period/interior and variable-period/near-boundary cases.
Variable periods have a known 50 ppm modulation; this is a different physical clock
construction, not applying two clocks to the same observations. A separate test
deliberately applies an incorrect clock scale and confirms a position discrepancy.
This does not identify the period represented by NASA's logged increments.

Six nuisance parameters are free: initial pitch, initial eastward velocity, Z gyro
offset and gain, gravity correction and receiver latency. Other nuisance parameters
are fixed to their known synthetic values, including no upstream Earth-rate removal.
The same box and observations are used for both solvers. Each fixture is fitted from
zero and an opposed starting point. The common synthetic position scale is 1 cm,
with no random noise. Prediction tolerance is 2 mm; objective tolerance above the
known-parameter reference is 0.01. These are software checks, not significance levels.

## Results

| True model | Construction | Solver | Passed | Largest position error (m) | Native sweeps |
|---|---|---|---:|---:|---:|
| sphere_rotating | nominal | original | 2/2 | 4.572913867509711e-06 | 82 |
| sphere_rotating | nominal | verified | 2/2 | 4.572982808671217e-06 | 93 |
| sphere_rotating | variable | original | 2/2 | 5.497171351761718e-06 | 110 |
| sphere_rotating | variable | verified | 2/2 | 5.497171351734965e-06 | 116 |
| sphere_still | nominal | original | 2/2 | 5.019288687169708e-06 | 81 |
| sphere_still | nominal | verified | 2/2 | 5.019152620405727e-06 | 85 |
| sphere_still | variable | original | 2/2 | 5.522125186401924e-06 | 108 |
| sphere_still | variable | verified | 2/2 | 5.522125186090851e-06 | 116 |
| flat_still | nominal | original | 2/2 | 5.205940466825125e-06 | 79 |
| flat_still | nominal | verified | 2/2 | 5.20567452053177e-06 | 87 |
| flat_still | variable | original | 2/2 | 5.529605927021372e-06 | 113 |
| flat_still | variable | verified | 2/2 | 5.529605540443351e-06 | 115 |

The largest returned-track error is **5.52961e-06 m**. Finite-interval navigation
uses a midpoint approximation, so exact continuous input integration has a small
nonzero reference error. All fitted objectives and reference errors are retained in
[fits.csv](fits.csv), with complete fit diagnostics in the saved report artifacts.

At the known parameters, the largest reference position error is
4.21112e-05 m. The two native
implementations agree to 0 m.
Automatic derivatives agree with separate central value differences within
8.57e-09 m per normalized
parameter unit. All six fixtures have off-packet receiver epochs. Conditioning and
singular values are saved; a numerical rank cutoff is not scientific identifiability.

The largest parameter difference from the injected reference is 0.646787
in units of its bound. Calibration recovery must be assessed separately from prediction
recovery: discretization error and weakly constrained parameters can shift the best fit.
No claim of uniquely recovered instrument calibration or global optimality is made.

The report charged exactly 24 starts, with no retries. There were **1275 native
sweeps**, including independent fixture checks and final prediction checks, within
the declared finite allowance. Ordinary unit-test invocations are separate from this
report's ledger. All results, including failures if any, are retained.

## What remains

These short six-parameter equatorial controls do not qualify every nuisance direction
in the 27-parameter archival fit, long-record conditioning, alternative processing or
independent-flight prediction. Nor do they explain the NASA Z gain/offset boundaries.
Next test the difficult calibration directions and full initialization at a finite
software budget before preparing matched observed gain–bias profiles. Those observed
profiles require a separately approved allowance; no corpus rerun is started here.
See the [focused analysis plan](../ILVIS0_DIAGNOSTIC_PLAN.md).

The public first-pass result remains 12 globe preferences, no completed flat preference
and 41 unresolved stretches. A successful software control does not turn those
exploratory comparisons into calibrated scientific detections.

Rebuild documentation without starting fits:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-geographic-controls-20261011/build_report.py --package-only
```
