# Modeling the recorded flights while instrument questions remain open

We are comparing the three Earth models with the six prepared airborne recordings.
An instrument inquiry has been sent; analysis continues under explicit assumptions
while a response is pending.

Each model predicts motion from the IMU's recorded turning and acceleration and
compares it with positions from the embedded GPS receiver. All 200 Hz packets remain
in the calculation, including tiny aircraft corrections. The fused navigation
answer is not used as a measurement or orientation constraint.

The window is the longest complete contiguous interval from the earlier frozen
selection, with usable GPS support, chosen before fitting. Six recordings cover
three configurations; the earlier 26 October 2010 scale-stability failure remains.

## Assumptions

The six files use the investigated IMU6 angle and velocity conversion hypotheses;
exact hardware calibration is not established. Initial tilt comes from raw force
and heading starts from GPS ground track. Both are fitted, rather than treated as
known aircraft orientation. Mounting and initial orientation share a gauge.

| Quantity | Assumed development envelope |
|---|---|
| Initial roll/pitch; yaw | ±10 degrees; ±180 degrees |
| Initial velocity; position | ±20 m/s; ±100 m per axis |
| Gyro bias; gains | ±20 degrees/hour; ±2% per axis |
| Acceleration bias; gains | ±0.25 m/s²; ±15% per axis |
| IMU-to-GPS antenna lever arm | ±10 m per axis |
| Timing offset | ±0.15 seconds |
| Gravity | 9.81 m/s² plus/minus 0.05 m/s² |

These are assumptions, not measured specifications or confidence bounds. The fit
assumes 200 Hz integration. Timestamp-derived intervals are evaluated at the fitted
parameters to expose sensitivity, without refitting.

GPS error assumptions are 1 m horizontal/3 m vertical, 60 s temporal correlation, common
offset and linear drift, plus an independent 0.3/0.3/0.7 m floor. A larger 10/30 m, 300 s
assumption is evaluated at fixed fitted parameters. All candidates use the same
coordinate covariance. Receiver latitude/longitude and covariance conversion use
conventional GPS geometry: this is a conditional inertial-motion comparison,
not a fresh GPS-ranging adjudication of Earth's shape.

## Unknown processing

Raw archive provenance does not establish corrections inside Applanix before logging.
All candidates allow a fraction between zero and one of the conventional Earth-rate
vector to have been removed. Reconstruction uses the SAME conventional Earth vector
for every candidate, including stationary models; physical Coriolis remains that
of the candidate being tested.

A fourth rotating-globe fit fixes subtraction at zero. It checks this additional
nuisance parameter; it is not a matched three-model comparison under a second
processing hypothesis. Transport subtraction, filtering, changing biases, off-axis
gains and exact onboard coning/sculling remain outside this first finite pass.

## Limits and interpretation

The run allows 24 starts across six files, 200 total evaluations per start including
derivatives and diagnostics. Interrupted starts count. Nonconvergence and parameters
at bounds remain visible. An unconverged fit cannot establish which candidate has
the smallest achievable error; local rank does not establish global identifiability.

**Completed:** all 24 fits ran without parsing or numerical failures. They cover
about 48.8 minutes across the six instrument recordings. None converged before its
evaluation allowance. These are recorded files, not six independent statistical
trials; simultaneous instrument streams can overlap.

The following RMS position errors describe the best evaluated points, in metres
north/east/up. They are not fully optimized likelihoods and cannot rank the models.

| Recording | Rotating globe | Stationary globe | Stationary disc |
|---|---|---|---|
| 14 April 2009 | 0.63 / 0.84 / 0.22 | 1.18 / 1.27 / 1.68 | 0.57 / 0.26 / 0.17 |
| 16 September 2014 | 9.91 / 9.59 / 1.77 | 67.06 / 69.40 / 22.50 | 33.56 / 17.85 / 9.00 |
| 26 October 2010 | 373 / 596 / 136 | 550 / 920 / 368 | 756 / 8,635 / 416 |
| 20 November 2010 | 0.31 / 0.16 / 0.70 | 0.68 / 1.35 / 0.63 | 5.77 / 5.94 / 0.95 |
| 24 September 2015 | 0.35 / 1.01 / 0.91 | 64.83 / 12.21 / 1.10 | 9.89 / 22.29 / 1.43 |
| 20 September 2017 | 1.13 / 0.81 / 0.26 | 3.29 / 1.05 / 0.25 | 6.68 / 39.19 / 1.44 |

Good positional agreement is attainable under several models in at least one
recording. Poor agreement in other files may reflect incomplete optimization,
instrument assumptions or unmodeled processing. The October failure is preserved.
The [full comparison](comparison.csv) includes the fixed-subtraction control,
parameters at bounds and covariance sensitivity.

Outputs retain residuals, parameters, correction fraction, convergence, assumption
sensitivity and hashes. There is no calibrated rejection or winner claim. Thirteen
new focused checks and fifteen existing estimator checks pass, including accelerator
agreement with the Python reference for small pitch motion and partial packets.

After preserving the six outcomes, inventory all 232 kept originals and extend the
conditional investigation where conversion, timing and receiver support can be
stated. Unsupported configurations remain recorded and preserved. Prior simulated
flight thresholds do not become calibrated for this dataset.
The inventory is now complete: 129 IMU6, 5 IMU8 and 98 IMU21 files. The
[corpus continuation](../ilvis0-corpus-modeling-20261008/README.md) states the new
finite scope and the solver changes prompted by the six-file evaluation limit.
