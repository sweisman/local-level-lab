# Testing an IMU for slow stationary rotation

An **IMU (inertial measurement unit)** measures turning and acceleration. The stationary
crowdsourced experiment needs sensitivity to a horizontal rate of at most about
15 degrees/hour. No consumer unit has yet demonstrated that capability in this project.

## Check the data and response

Use an instrument-test session to check raw decoding, timing, setting readbacks, link
continuity and an independently measured turn angle. Test the actual device and settings.

The essential control is a **known slow turn**, measured independently of the IMU.
Record both directions at several imposed rates. Check automatic zeroing off and on;
a successful register readback alone does not establish that slow motion survives.
Never qualify a unit by how closely it matches the expected Earth-rate curve.

The finest supported digital range reports roughly 27 degrees/hour per count.
Measure whether averaging actually recovers imposed rates below that step. Repeating
a fixed rounded value cannot reveal an arbitrarily small signal.

## Check stability and reversals

Make still recordings of at least two hours and repeated warming/cooling cycles.
Keep temperature and interruptions. The [persistence diagnostic](INPUT_PERSISTENCE.md)
helps show how long errors last and whether longer averaging still improves stability.

Repeat the [same-face A/B protocol](PROTOCOL.md) on different days. Use known holder
stops and record leveling/alignment uncertainty. Reversals cancel constant offsets;
temperature changes and nonlinear drift can still imitate an orientation difference.
Compare two independently tested IMUs when possible.

Test Bluetooth interruption, background recording and clipping during slow hand turns.
Retain failed controls. Hardware specifications and NASA survey results cannot substitute
for consumer measurements.

## Scientific use

The current stationary output is a development diagnostic, with no validated detection
threshold or population pooling. Duration and uncertainty must be chosen from independent
instrument controls, not from whichever recording produces an appealing result.

The [technical bench record](BENCH_TECHNICAL.md) preserves earlier passenger-protocol
checks. Its legacy quality tiers and certificates do not automatically qualify the
stationary experiment. See [validation](VALIDATION.md).
