# Testing the instrument before flying

An **IMU (inertial measurement unit)** combines instruments that measure turning and acceleration.
Here we test whether its turning measurement is reliable enough for the experiment.

A successful recording does not prove that its IMU can measure the very slow turning this
experiment needs. Each physical instrument must be tested on the ground before its flights
can contribute to the main research result. Tests of the software do not replace these measurements.

No real instrument has completed this validation in the current project work. The acceptance
limits are provisional until enough units have been measured. Keep failed tests as well as
successful ones; they show what the equipment can actually do.

## Start with a simple recording

In the app, open Settings, choose the instrument, and write and verify its settings. Then use
Bench tests to record it resting on a firm table. Check that the expected data arrives, the
connection stays alive, and the device is using the settings requested.

An analyst also checks that the saved messages decode correctly, that timing and sample counts
are consistent, and that the reported measurement range is used. A known 90-degree hand turn
and a stationary accelerometer reading help expose incorrect scale factors.

## Make sure slow rotation is preserved

This is the essential check. Some gyro firmware treats a slow steady reading as an error and
zeros it automatically. That would erase the effect the experiment is trying to measure.

Put the IMU on an apparatus that turns slowly at a rate measured independently, such as a
geared turntable with an angle scale. Record clockwise and counterclockwise runs. Comparing
those directions helps cancel the IMU offset and any background rotation.

Repeat with automatic zeroing disabled and enabled, then leave it disabled for flight recording.
The disabled setting must preserve the imposed slow motion. The test must establish what the
setting does rather than merely show that a register accepted a command. Do not use agreement
with an expected Earth rotation as the instrument qualification test.

## Check stability and repeatability

Make a still recording of at least two hours, ideally at steady room temperature. This shows
how much the readings wander when the IMU is untouched, including changes that short
recordings hide.

The research diagnostic in [measuring how long errors last](INPUT_PERSISTENCE.md)
is now ready to examine these still recordings. It reports whether variation persists
over time and how much longer averaging helps, with gaps preserved. GPS can be examined
alongside the IMU when available. These measurements help choose defensible uncertainty
assumptions; the diagnostic itself does not certify an instrument or an Earth-model result.

Next, repeat the same-side-up reversal test: keep the IMU level and turn it to face the
opposite way between still placements. Repeat on at least three days. The question is whether
it gives repeatable measurements with honest uncertainty, not whether it produces a preferred
Earth-model answer. Two independent instruments tested side by side provide a useful cross-check.

Repeat the full calibration sequence too. Its horizontal measurement should be consistent
with the reversal test. The vertical measurement can be confused with other IMU effects
and must not be presented as an independent measurement of Earth rotation.

## Check range, Bluetooth and temperature

A smaller gyro range can resolve smaller changes, but a hand turn can then exceed its limit.
Test several ranges, and check that normal slow turns do not overload the chosen setting.
Do not choose a range from its specification alone.

Deliberately interrupt Bluetooth during a bench recording. Check that it reconnects, missing
data is reported and the later timing remains correct. Test at the distance the phone and
IMU will have in the cabin.

Record at least two slow warming-and-cooling cycles. One warm-up cannot reliably separate a
temperature effect from ordinary drift with time. Temperature tests characterize the device;
a poorly understood effect must remain an uncertainty rather than be treated as a correction.

## Before using flight results

Retain the original bench recordings and have the full evidence reviewed for the actual
physical unit and settings being used. This review must precede the flight; a later good test
cannot retroactively certify an earlier measurement. A flight quality label alone is insufficient.

The [technical bench checklist](BENCH_TECHNICAL.md) gives exact report fields, tolerances and
measurement procedures. [Research-record eligibility](PRIMARY_CORPUS.md) explains the approval
process. Use the [participant guide](PROTOCOL.md) when preparing a recording.
