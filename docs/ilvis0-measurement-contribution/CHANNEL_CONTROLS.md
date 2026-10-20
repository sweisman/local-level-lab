# Separating gyroscope and acceleration evidence

An **IMU (inertial measurement unit)** measures turning with gyroscopes and
specific force with accelerometers. The present flight reconstruction uses both.
To learn what each contributes, a comparison must genuinely remove the selected
measurement rather than quietly replace it with the instrument's finished
navigation answer.

The first **25 software checks pass**. They use constructed vectors and rotations,
not recorded flights, fitted Earth models or fused navigation. They establish the
geometry needed to design the next comparison. They do not change the 53-stretch
findings or qualify a new observational likelihood.

## Without the gyroscope

Suppose receiver positions and a declared physical model supply the force needed
to follow a trajectory. An accelerometer measures that force in the instrument's
own axes. Matching the two force directions constrains two components of
orientation. Turning the instrument about that force direction leaves the
accelerometer prediction unchanged. Its remaining angle can also vary over time;
unchanged acceleration therefore does not mean unchanged angular motion.

Gyroscope observations constrain those changes. Supplying fused attitude after
removing the gyroscope would put related inertial information back into the
comparison. Assuming aircraft heading equals GPS course would instead add an
alignment assumption; the two are not interchangeable measurements.

A useful first acceleration-only comparison avoids inventing that missing
orientation. **Rotations preserve force magnitude**, so compare measured
acceleration magnitude with the force magnitude required by each trajectory
model. A mismatch cannot be hidden by choosing another orientation. Matching
magnitudes, however, does not determine orientation or show that a complete
gyroscope/acceleration history is consistent.

This control retains receiver-coordinate, gravity and acceleration-calibration
assumptions. It asks whether those non-gyro inputs alone can produce a model
distinction. It is not a coordinate-free curvature test, and its result cannot
be subtracted from the original fit cost to assign a percentage to gyroscopes.

## Without the accelerometer

For any specified orientation and receiver-derived force requirement, a body-frame
force history can be invented that reproduces the requirement. That invented
history is a replacement assumption, not an observed accelerometer stream.
Initial tilt must also cease using omitted accelerometer observations.

An acceleration-free test therefore needs an independently justified force or
orientation constraint, or must report the remaining ambiguity. No such
constraint is supplied by these controls. They do not establish that either
Earth geometry can fit the actual data without acceleration observations.

## Equations and checked cases

Let \(R\) rotate instrument axes into local north/east/down axes, \(f_b\) be
body-frame specific force, and \(F\) be the navigation-frame requirement. Then
\(R f_b=F\). At one epoch the rotation derivative has rank two for nonzero
force; rotation about \(F\) is its unobserved direction. This is a local
geometric statement, not the rank of an entire flight fit.

With velocity components \(v\), their derivative \(\dot v\), gravity \(g\),
background angular rate \(\omega\), and transport rate \(\tau\), the declared
navigation equations require

\[
F=\dot v-g+(2\omega+\tau)\times v.
\]

The rotation-invariant diagnostic is \(\lVert f_b\rVert-\lVert F\rVert\), in
metres per second squared. It is not yet a whitened residual or a calibrated
test statistic. Every candidate must supply its own declared metric, transport,
background and gravity assumptions. No standard background rate is silently
inserted by the helper.

The checks cover arbitrary and opposite force directions, nearly opposite
directions, proper rotations, a time-varying unobserved angle, unequal force
magnitudes, rank and derivative signs, explicit invented-force reconstruction,
gravity/Coriolis/transport signs, free fall, and invalid inputs.

Implementation: [channel helpers](../../analysis/lll/ilvis0_channel_controls.py)
and [known-answer tests](../../analysis/tests/test_ilvis0_channel_controls.py).
The helpers contain no archive reader, optimizer or model-selection gate.

## Qualification progress and next steps

The independent [18-case trajectory-force matrix](../ilvis0-channel-trajectory-controls-20261019/INTERPRETATION.md)
has now passed. The calculations agree for stationary, slow, straight,
direction-changing and climbing motion without using gyro or fused-attitude
observations. The following [receiver-derivative adapter](../ilvis0-channel-trajectory-controls-20261019/DERIVATIVES.md)
passes 22 mathematical checks, including joint covariance and overlapping-window
dependence. These checks do not establish observational uncertainty.

The subsequent [46-case error-budget diagnostic](../ilvis0-channel-error-budget-20261019/INTERPRETATION.md)
quantifies approximation, nonlinear response and acceleration-aggregation errors.
It preserves 27 of 108 candidate/window combinations that fail its declared
approximation screens. The subsequent [calibration control](CALIBRATION.md)
shows that one permitted constant gain erases wrong-model scalar differences on
the constructed straight leg. All nine combinations pass that limitation check;
it is not an observed calibration measurement. The [72-case local matrix](../ilvis0-scalar-calibration-controls-20261019/INTERPRETATION.md)
now covers changing motion with all seven calibration directions. Its surviving
local differences and infeasible wrong-model linear corrections require a
bounded nonlinear check before recorded-data use.

The subsequent [nonlinear study](../ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md)
passes all known-answer starts but only 32/72 full matrix comparisons. The later
[certificate candidate](../ilvis0-scalar-certificate-controls-20261019/INTERPRETATION.md)
qualifies all 72 mathematical comparisons with feasible constructions and bounded
fits kept distinct. Observational timing and uncertainty still block recorded-data
channel fitting. Independent [quantization/period controls](QUANTIZATION.md)
pass 17 checks; their deterministic bounds are not a statistical error model or
a continuous-force upper bound.

1. Preserve the completed exact-trajectory controls, including indistinguishable
   stationary cases and every incorrect-model outcome. They qualify the force
   calculation, not a recorded-data likelihood.
2. Assess receiver-trajectory approximation and propagate its joint uncertainty
   through force and magnitude. Specify shared calibration freedoms, raw-increment
   averaging, synchronization and initialization dependencies. Noise in differentiated
   positions must not be treated as an exact force observation.
3. Follow the completed local calibration matrix with bounded nonlinear checks
   of the surviving temporal distinctions before freezing a recorded-data comparison.
   Reuse preselected intervals; do not choose stretches by favorable force residuals.
4. Preserve the original full-position results and the unresolved horizontal-only
   sensitivity result separately. Further timing-grid expansion is deferred.

This software step starts no new archived-data fit, synthetic flight campaign,
free rotation-field analysis or population calibration.

[Measurement contributions](README.md) · [Next analyses](../NEXT_STEPS.md).
