# Keeping aircraft motion in the measurement

The joint IMU/GPS motion model is implemented and its controlled checks pass. A separate
six-file preparation also completed: **593,682 native IMU packets** passed strict framing
and original-hash checks. It reproduced all **2,930** previously complete diagnostic seconds;
**2,928** have checksummed GPS observations near both ends. No fused navigation supplied
the observations, no Earth-model outcome was fitted, and all 232 originals remain stored.

## Why this advances the experiment

A short aircraft correction can disappear from an average while still changing the IMU's
relationship to gravity. Merely adding gyro readings also loses the effect of rotations
about different axes occurring in sequence. The new code follows each 200 Hz increment,
rotates acceleration as the instrument turns, and accumulates its effect on velocity and
position. It preserves those effects when intervals are combined.

One controlled test pitches the IMU by **0.1 degree and back within one second**. The final
orientation equals the starting orientation, but the motion model retains the correction
and reconstructs the known translation correctly. A separate control has zero summed angle
increments but a nonzero final rotation because its rotations occurred about different axes.
These are deterministic software controls, not additional simulated flight campaigns.

The real recordings show why this matters. Across the prepared one-second intervals, the
largest difference between finite rotation and rotation inferred from summed angles is
about **11.5 arcseconds**. Rotating specific force instead of adding its body-axis values
changes the integrated velocity by as much as **0.368 metres/second**. These are motion
processing differences, not Earth measurements, intrinsic IMU noise or evidence for a model.

## The joint physical model

The model takes raw angle/velocity increments, an initial aircraft attitude and velocity,
sensor calibration, gravity and a candidate coordinate geometry. It predicts the evolving
attitude, velocity and position that GPS could constrain. It separates aircraft rotation,
Earth rotation and rotation of the local frame while travelling. Gravity and Coriolis effects
enter the velocity equation explicitly. Body heading is a state; it is not set equal to the
receiver's ground track.

The two globe candidates use their stated globe coordinate metric. The disc candidate uses
the project's pole-centred disc geometry and requires an explicit distance scale. Reported
GPS coordinates and heights carry their receiver conventions; mapping them into each
candidate is conditional, rather than treating GPS as independent proof of Earth's shape.

Calibration and mounting bounds must be supplied explicitly. The code rejects values outside
them and supplies no invented sensor-performance defaults. The GPS antenna and IMU may be
at different points on the aircraft, so their lever arm is an explicit part of the model.
Its motion correction uses aircraft rotation relative to the local frame, not raw inertial
gyro readings indiscriminately. Actual antenna/IMU lever values remain unestablished here.

The forward model also makes recorded processing explicit. Its current navigation integrator
requires the unsubtracted-increment hypothesis. Its joint increment predictor exposes separate
Earth-rate and transport-rate retention hypotheses, rather than assuming they are established
for Group 4. A control shows that Earth-rate subtraction can erase the expected stationary
gyro term. This checks the consequence of that processing assumption; it does not identify
which processing the archive actually used.

## What the prepared data preserve

Each interval retains its raw signed integer sums, packet boundaries, logged installation
epoch, composed rotation, rotated specific-force integral and position integral. It carries
both accumulated-header and nominal-200-Hz durations. Bias-free angle and velocity increments
do not need division by a jittery timestamp to be integrated; elapsed time still matters for
position, gravity, Earth/frame terms and bias corrections. Neither clock hypothesis is
silently selected as scientific truth.

Each GPS endpoint retains the checksummed GGA sentence, receiver-stream and packet offsets,
reported height/geoid fields and actual receiver epoch. The corresponding IMU endpoint can
differ by milliseconds: the offset is recorded, not hidden by pretending the observations
are simultaneous. Missing endpoints stay missing; no GPS or IMU measurement is interpolated.
Future fitting must account for endpoint timing, latency and measurement uncertainty.

The within-packet calculation assumes constant body rate and specific force over that packet.
It integrates that hypothesis exactly; this does not establish whether the manufacturer
already applied coning, sculling, filtering or other corrections. Changing bias, gain or
processing hypotheses can require returning to the original packets. Earlier scale failures,
including the marginal 26 October 2010 gyro check, remain unchanged. These factors are
diagnostic inputs, not a new physical-decoder or level-flight acceptance policy.

## What remains before an Earth comparison

The forward model is ready for an estimator, but real aircraft initial attitude, sensor
errors, gravity/lever/timing uncertainty and defensible bounds are not yet established.
Recorded correction behavior also remains unresolved. Agreement with fused navigation or
with a preferred Earth prediction cannot independently settle those assumptions.

Next, validate the estimator's motion and calibration constraints using observations that
do not select an Earth outcome, and resolve the recorded processing hypotheses. Then test
pairwise identifiability through the joint model before the bounded empirical comparison.
Globe versus disc remains a worthwhile question even when the complete three-way question
is unavailable. No existing synthetic decision threshold transfers to these recordings.

## Reproducing the work

Code: `analysis/lll/ilvis0_forward.py`; launcher:
`analysis/tests/ilvis0_forward_worker.py`. The completed output is
`data/ilvis0-forward-20261007/` and must not be resumed with changed source. This evidence
directory preserves its manifest, source snapshots, completion, compressed full report,
per-file inventory and compressed motion factors with receiver endpoints.

Thirty-two focused tests passed: sixteen new forward/integration/control/source/recovery
checks and sixteen preceding observation/installation checks. They include independent
numerical quadrature, composition, rotation signs, gravity/rotation/Coriolis consistency,
candidate metric mappings, explicit bounds/processing, timing offsets and corrupt recovery.
This is numerical/software validation, not independent airborne motion-domain validation.

The general approach of integrating IMU observations between measurement epochs while
respecting finite rotations is described in
[Forster and colleagues' preintegration paper](https://arxiv.org/abs/1512.02363).
The constant-body interval integrals and conditional archival equations here are repository
implementations; that paper supplies no evidence about Applanix processing or this dataset's
independence.
