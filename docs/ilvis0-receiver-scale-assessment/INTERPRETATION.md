# A shared error source, separate from the Earth candidates

All **six predeclared calculations completed** using the first 292 receiver
positions of one previously studied IMU21 recording. Later GPS positions,
gyroscope observations and Earth-model residuals were absent from the assessment.
No Earth-model fit was run.

The calculation puts an upper bound on a common multiplier of each declared
receiver-error model. It does not measure receiver accuracy. The Gaussian
covariance shape is supplied as an assumption; the calculation cannot prove
that assumption from one flight.

| Approximate correlation time | Cubic reference | Degree-five reference | Degree-seven reference |
|---|---:|---:|---:|
| 10 seconds | 2.269 | 1.326 | 0.309 |
| 300 seconds | 5.463 | 3.963 | 1.127 |

These are dimensionless scale upper bounds. Each multiplies all standard
deviations in its own declared law. A polynomial that describes the aircraft
path poorly can inflate the bound, as the large change across reference degrees
illustrates. Both the reference and correlation assumptions matter. All six
results are retained; none is selected using an Earth-model preference.

The chart is fixed before calculation, including a longitude scale at 60°
latitude. It is distinct from the receiver-dependent coordinate metric of the
older fits. The bounds cannot simply be substituted into those fits, and no
simultaneous observational coverage or calibrated detection follows.

## What this adds

A poorly fitting Earth candidate cannot give itself a larger noise allowance
through its own residuals. This training-only component is reproducible, uses
exact residual arithmetic and preserves all declared covariance alternatives.
The preceding software qualification includes independent exact matrix checks.

The new assessment spent six identities and 5,256 scalar innovation epochs,
with zero native predictions, optimizer starts or original IMU reads. The
completed freeze cannot be restarted or supply unused work to another study.

## What remains

The 53 full-position comparisons remain **53 globe preferences, zero flat
preferences and zero unresolved**. This error-source calculation adds no
independent flight, model winner or statistical significance claim.

The main prediction obstacle remains the broad nonlinear calibration ranges.
The generated contraction kept the true parameters but left future ranges
hundreds of metres wide. Work must preserve joint calibration constraints and
reduce the nonlinear remainder without discarding feasible parameters or using
withheld observations. Global numerical error, absolute predictive adequacy
and untouched confirmation also remain open.

[Every calculation and reference residual](README.md) · [Frozen scope](PLAN.md) ·
[Exact mathematics](../ilvis0-exact-scale-v2/INTERPRETATION.md) ·
[Saved withheld-position evidence](../ilvis0-saved-prediction-comparison/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
