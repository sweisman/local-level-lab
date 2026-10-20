# Receiver positions give a more useful motion check

The assessment completed all 2,048 preselected centers: 2,046 supported windows
and two unsupported edges. The same 1,507 windows retain the earlier airborne
classification. No gyroscope measurements or model-fit results were inspected.

Among those airborne windows, **96 position-derived trend intervals lie wholly
inside ±0.02°/s even allowing arbitrary temporal correlation**. The earlier
velocity-derived calculation confirmed none. Under the independent-error
assumption the new count is 606; under the supplied correlation sensitivity it
is 531. These different counts show why the error assumptions matter.

Point estimates themselves are similar: 756 windows exceed the turn cutoff,
versus 749 in the earlier velocity trend. Their median absolute course-rate
difference is 0.00129°/s. The main gain is usable uncertainty for some windows,
not evidence that the aircraft followed a fundamentally different path.

The median absolute difference between position-derived and mean reported
velocity is 0.022 m/s north and 0.013 m/s east. Median cubic residual RMS is
0.0064 m north, 0.0036 m east and 0.0138 m in height. Median residual lag-one
correlations are about 0.56–0.60. Polynomial fitting itself affects residual
correlation; these values do not identify the true receiver-error law.

## What remains open

The 96 intervals are **sampled trend checks, not 96 eligible stretches**.
Centers are spaced apart; this assessment does not establish continuous quiet
flight between them. A noise-free fitted trend also differs from instantaneous
aircraft motion. No bound on the missing motion was supplied, and the reported
receiver covariance remains uncalibrated. Position and velocity are outputs of
the same receiver solution, not independent position truth.

The existing ESA inventory still has zero eligible intervals. A replacement
selection requires a separately justified and frozen motion/error policy and
complete coverage. The seven confirmation groups remain protected.

The run took 43.5 seconds, decoded 64,080 epochs from one receiver file and
reconciled all 2,048 window reservations. It performed 2,046 position assessments,
point conversions and independent residual fits, within each 2,048-operation
ceiling. No original IMU was read and no Earth model was fitted.

[All window results](windows.csv) · [Frozen scope](PLAN.md) ·
[Next work](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
