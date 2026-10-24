# Compose native packet errors over complete generated histories

The single-step derivatives and shared-noise innovations are qualified. This
next gate combines them over generated histories using the existing motion
equations. It does not fit a flight or change the completed noisy controls.

Maintain an extended-precision nominal state and fifteen error coordinates:
nine attitude/velocity/coordinate errors plus six sensor-frame changing biases.
Use actual packet intervals. White increment noise and OU integral/endpoint
innovations follow the separately checked measurement-noise law. Stationary
bias variance initializes the bias states; pose is known in these controls.
Static calibration parameters remain fixed and explicit.

The bridge receives corrected increments. Apply the declared correction
scales to raw sensor errors, with the correct negative sign for true-minus-
nominal pose error. The bias states retain the positive measurement-bias
convention. Preserve OU integral/endpoint covariance and all six axes.

Accumulate gap transitions and noise loadings between receiver queries.
Preserve rank-deficient and zero-noise components using covariance-equivalent
square-root composition, without jitter, variance floors or eigenvalue clipping.
Row scaling may improve numerical conditioning; zero rows must remain zero.

A query inside a packet uses the same full-packet increment error as its
endpoint. Use the existing binary64 query/packet association and fraction,
then extended-precision partial increments and time products. Combine gap and
packet noise into the explicit shared-observation mode. Do not invent
independent noise on the two pieces. Reject unsupported query associations
instead of discarding observations or silently changing their times.

Check nominal query observations against the existing complete wider path.
For short histories, compare covariance with independent nonlinear finite
differences along Gaussian driver directions, including initial bias. Retain
all candidate/processing/gravity combinations and test interior packet queries.
Test zero/rank-deficient noise, unequal packet intervals, input preservation,
invalid associations and exact work accounting. A longer generated check
uses every packet, rather than extrapolating one local derivative.

The qualification allowance is twelve generated candidate/processing/gravity
combinations, at most 600 packets per long case and four packets per short
case, 24,000 native calls, 32,000 conservative packet steps and two cached
builds. Use one numerical thread and a cooperative 30-minute ceiling. No
random draws, optimizer starts, original reads or protected reads are allowed.
Charge native work/builds before execution. Freeze a fresh source/environment
and retain any failed qualification without resetting its allowance.

The first composition gate uses an explicitly supplied independent receiver
error loading. Persistent receiver errors and uncertainty in fitted calibration
parameters remain separate requirements. Passing generated linearization and
covariance controls does not establish nonlinear coverage for observed flights
or authorize opening confirmation groups.

[Single-step result](README.md) ·
[Shared-noise covariance](../integrated-noise-covariance/JOINT_PLAN.md) ·
[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
