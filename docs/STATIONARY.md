# Measuring a stationary rotation field

This is the secondary, crowdsourced branch of Local Level Lab. The primary branch
analyzes professional NASA airborne recordings. An **IMU (inertial measurement unit)**
measures turning and acceleration; here it rests on a solid surface instead of moving
with an aircraft.

The question is: **can independent IMUs recover a consistent horizontal rotation
component, and does it change with latitude?** This is a field measurement, not a
standalone test of globe versus flat, and it does not identify the field's ultimate cause.

## Why reverse the IMU?

Mark a horizontal positive sensor axis. In position A it points approximately toward
true north. In position B it points the opposite way, with the same face up.

For a stable offset, the readings are approximately:

```
A: sensor offset + external horizontal rate
B: sensor offset − external horizontal rate

signed rate = (A − B) / 2
```

Reversal cancels a constant sensor offset. Keeping the same face up helps preserve
gravity-related sensor errors. Neither step cancels every error: changing temperature,
nonlinear offset changes, tilt, imperfect turns and support motion can remain.

The development protocol uses A–B–B–A twice. Its balanced timing helps separate a
linear offset change from the reversal signal. Actual block times are used in the fit;
a fixed number of minutes is not assumed when calculating elapsed time.

## Measure first, compare with latitude afterward

The per-recording diagnostic receives block positions, times and gyro readings.
It does **not** receive latitude or an expected rotation rate. It fits a signed rate,
a constant offset and a linear offset change, with equal weights per settled block.
It preserves negative and zero estimates rather than turning noise into a positive
magnitude. Thirty seconds at each block edge are excluded; originals remain intact.

The app stores location and alignment separately. This computational separation is
not full researcher blinding: the public upload still includes the location. A stronger
study would seal the estimator, exclusions and per-recording output hashes before
revealing locations to the population analysis.

Only afterward would a separately validated population analysis compare signed rates
with latitude. The standard rotating-Earth prediction is
**northward rate = A × cos(latitude)**, with A near 15 degrees/hour.
Fit A freely; do not force the expected value or calibrate a sensor by matching it.
True-north alignment and its uncertainty must be accounted for: an axis misaligned
by angle ψ measures approximately A × cos(latitude) × cos(ψ).
[VectorNav's gyrocompassing explanation](https://www.vectornav.com/resources/inertial-navigation-primer/theory-of-operation/theory-gyros)
describes the standard horizontal prediction.

The northward horizontal component has the same sign in both hemispheres. Its
vertical component changes sign, but that is outside the primary consumer target.
This experiment does not seek to distinguish solar from sidereal rotation rates,
measure polar wobble or estimate tiny altitude effects.

## What is implemented, and what remains?

The app creates stationary recordings, guides eight still blocks, preserves original
Bluetooth bytes and block markers, and supports sharing or consented public upload.
Location can be entered manually; continuous GPS and flight details are unnecessary.
The Python analyzer produces a preliminary signed-rate diagnostic and a readable report.
Incomplete sequences, invalid timestamps, large gaps and failed level/stillness checks
withhold the rate. Repeated attempts remain in the original recording; the last visit
to a named block is used, without selecting by gyro agreement.

**Consumer sensitivity and uncertainty have not yet been established.** At the finest
currently supported gyro range, one reported count is about 27 degrees/hour—larger
than the target. Averaging can recover smaller means when the output genuinely samples
them, but cannot undo automatic zeroing, fixed quantization or changing systematic error.

Next work is physical slow-turn validation, temperature/stability measurements,
alignment checks, defensible uncertainty and independent replication. The current
diagnostic has no detection threshold, confidence interval or population pooling.
It always abstains from a scientific decision. Existing aircraft thresholds and bench
certificates do not qualify this new experiment.

Recordings from the same physical IMU share errors. Future pooling must preserve
instrument, day and site grouping; eight blocks are not eight independent confirmations.
Report nulls, negative estimates, failed recordings and exclusions alongside successes.
Broad geographic coverage is valuable only with adequate sensitivity and honest uncertainty.

See the [participant protocol](PROTOCOL.md), [instrument checks](BENCH.md),
[validation plan](VALIDATION.md) and [privacy policy](../PRIVACY.md).
