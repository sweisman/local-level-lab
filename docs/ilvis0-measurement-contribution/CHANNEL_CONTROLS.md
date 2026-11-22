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

The [ESA earlier-only direction alignment](../prediction-observed-development/ESA_FORCE_DIRECTION_TRANSFER_RESULT.md)
uses the measured gyro to put all force directions in one frame. One
rotation fitted to the first eight directions transfers better for the
globe under nominal calibration. With one allowed accelerometer correction,
the retained-field comparison instead favors the disc. A justified
calibration range remains necessary to interpret this channel comparison.

A useful first acceleration-only comparison avoids inventing that missing
orientation. **Rotations preserve force magnitude**, so compare measured
acceleration magnitude with the force magnitude required by each trajectory
model. A mismatch cannot be hidden by choosing another orientation. Matching
magnitudes, however, does not determine orientation or show that a complete
gyroscope/acceleration history is consistent.

There is a sharper limit for a **gyro-free model with otherwise unrestricted
attitude**. On a continuous interval where both force vectors stay nonzero,
equal magnitudes at every instant permit some continuous orientation that maps
one vector onto the other. Continuous frames can be chosen along the two force
directions and one frame rotated onto the other; rotation around that direction
remains free. This construction supplies no independently measured aircraft
attitude or bound on how fast it changes. The recorded scalar envelopes overlap,
but that is not proof of exact equality under one shared calibration or of a
physically adequate flight. Additional rejection requires justified attitude,
motion or calibration constraints rather than an arbitrary gyro-free heading.

A [sampled-history construction](../../analysis/lll/ilvis0_gyro_free_path.py)
now makes that ambiguity executable. Three
[known-answer checks](../../analysis/tests/test_ilvis0_gyro_free_path.py)
build two different attitude histories that produce the **same complete force
sequence**, including an opposite-force step. The construction assumes exact
equal magnitudes and imposes no bound on attitude change; it is a geometry
control, not a reconstruction of any archived flight.

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

The [receiver-only support selector](SUPPORT_POLICY.md) and timed-GGA motion
adapter now pass 21 software checks. They record every candidate window and
choose the longest one meeting explicitly supplied motion limits, identically
for all physical models. No flight-specific threshold or recorded interval has
been frozen; this does not qualify a new observed-data fit.

A [joint force-magnitude covariance helper](../../analysis/lll/ilvis0_force_magnitude_covariance.py)
now carries a **supplied** receiver-position covariance through the
gyro-free force calculation. It keeps error shared by overlapping receiver
windows instead of counting them as independent. Eight checks pass, including
stationary overlap, moving-model sensitivity, a correlated-noise nonlinear
replay and abstention when required force is near zero.
This local linearization does not calibrate receiver error, trajectory
approximation, acceleration calibration or nonlinear coverage. It makes no
aircraft decision.

A [receiver-only bridge](../../analysis/lll/ilvis0_joint_receiver_force.py)
now applies the same timed-GGA window selection to all three models. It returns
their required force magnitudes and one covariance across both overlapping
windows **and candidate models**. The same GPS error can shift every candidate;
their prediction errors cannot be counted as independent. Five focused checks
pass.
This is a software control; it has not fitted a recorded flight or selected
an Earth model.
The dense bridge accepts at most 128 receiver epochs and conditions on the
windows selected from those same noisy positions. A whole-stretch comparison
needs a scalable joint error operator and a check of selection uncertainty.

A separate [structured projection](../../analysis/lll/ilvis0_structured_force_projection.py)
now carries a declared white, correlated, offset and drift receiver-error law
through the force magnitudes of all three models without building a full
receiver covariance. Six checks pass against the dense reference, including
coordinate transforms and a 2,000-epoch support. The GGA-only bridge now
connects this calculation to common selected windows: four further checks
match the dense bridge with and without coordinate transforms, admit 200
fixes, and abstain with no support. Each
local derivative window remains capped at 128 fixes, and total embedded
weights have a 128 MiB workspace guard. This does not establish the real
receiver-error law or account for selection uncertainty.
Each call requires one receiver block without gaps above the declared limit.
The [saved receiver-gap inventory](../ilvis0-receiver-gap-inventory/README.md)
screened all 53 preselected stretches: 52 enhanced-position streams each have
one uninterrupted block under the 1.5-second rule; one prior strict-decoder
failure remains. This establishes available receiver coverage, not the
receiver-error law or a matched gyroscope/accelerometer comparison. A software
adapter now accepts the receiver's enhanced-position timestamps, coordinates
and reported GNSS velocities while retaining their separate provenance.
Its three new checks and 31 existing bridge/support checks pass. No recorded
block has yet been evaluated through that adapter.

A [saved-window stability check](WINDOW_STABILITY_RESULT.md) now bounds how
often the GPS-only support choice survives **assumed** per-reading motion
errors. With ±0.05 m/s in speed and climb rate and ±0.05° in course, 1,580
of 2,194 chosen windows are guaranteed unchanged; with ±0.10 m/s and the same
course range, 1,111 are. The remaining choices are uncertain under these
bounds, not observed flips. The assumed ranges are not measured receiver
accuracy, and this does not propagate position error into force predictions.

The force geometry, bounded calibration controls, receiver-only window policy,
and recorded whole-history scalar assessment are complete. The latter excludes
none of the three models under its declared error envelopes. Its overlap is a
useful limit on what acceleration magnitude alone can establish; it is not a
complete gyro-free fit.

The remaining gate is a matched recorded-data channel comparison with one
shared calibration over each full selected history. It needs an observational
receiver-error law, uncertainty from selecting windows on noisy positions,
and a justified attitude or motion constraint if the gyro is omitted. It must
reuse the preselected stretches and keep the original full-position and
horizontal-only results separate. Until those inputs are qualified, the
scientific result is abstain rather than a claimed percentage of evidence from
the gyro.

The [direction-pair screen](../../analysis/lll/ilvis0_force_motion_screen.py)
handles one possible external motion bound. For each consecutive pair, it
compares the turn between corrected accelerometer directions with the turn
between the required force directions expressed in one common frame. The
difference, reduced by explicit direction errors, gives a lower bound on
how far the instrument attitude must rotate. A pair can violate an
independently supplied rate limit. Passing all pairs leaves the existence
of one compatible attitude history open. A violation at one calibration
does not exclude other allowed calibrations. The archive does not yet
provide a qualified rate limit for use in this screen.

The same software can also construct one nominal attitude path and check
its rate between the sampled epochs. A successful path is a feasibility
witness at the supplied calibration and nominal force directions. It
does not identify the attitude or enforce force direction between the
samples. Four generated checks cover exclusion, a feasible witness,
unobservable attitude, and unsupported zero force.

The [three-sample screen](FORCE_MOTION_TRIPLETS.md) also detects when two
individually possible steps require incompatible middle orientations. It uses
the fixed spatial axes of each candidate geometry. The archive still needs
independent motion and direction-error bounds before a recorded gyro-free decision.
The [whole-history check](FORCE_MOTION_HISTORY.md) connects those steps across
the complete sequence. It verifies a proposed nominal path or excludes it
under outward allowances for unresolved twist and direction error. A check
that falls between those results stays open.
On [two saved recordings](RECORDED_MOTION_RATE_RESULT.md), these directional
rate brackets overlapped across the four candidates in all 16 matched
settings. The result assumes fixed GPS paths and no calibration correction.

A [catalog check for outside motion evidence](MOTION_SOURCE_AUDIT.md)
found no timed LVIS images during either stretch. A listed same-flight
NCAR file may supply motion context for IMU21. Its campaign attitude
channels come from inertial navigation, and its one-second output leaves
motion within each second unresolved.

The [paired gyro clock comparison](PAIRED_GYRO_CLOCK_RESULT.md) checks whole
packets from two known overlaps. The shifts picked on earlier data reduce
later short-window gyro disagreement by at most 4.6%. The two overlaps give no upper
bound on the gyro errors or aircraft motion used in the channel controls.

[Measurement contributions](README.md) · [Next analyses](../NEXT_STEPS.md).
