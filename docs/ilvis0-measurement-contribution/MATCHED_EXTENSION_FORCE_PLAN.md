# Test the added flights without gyroscope measurements

Use the exact [prepared inertial and GPS inputs](MATCHED_EXTENSION_INPUTS_RESULT.md)
for the two added flights in the [matched forecast study](MATCHED_EXTENSION_FORECAST_RESULT.md).
Compare a necessary accelerometer-only inequality for the same four
candidates. The length of the measured specific-force vector is unchanged
by an unknown sensor orientation. Use the three accelerometer counts and
their recorded scale. Exclude gyro increments, fused navigation and
assumed attitude histories from the calculation.

At each original GPS report, consider the same 30-second window as in
the [earlier force calculation](MATCHED_FORCE_AVERAGE_PLAN.md). Require a
complete receiver window wholly on one side of the fixed cut. Keep only
accelerometer packets that fit inside the window under both clocks and the
full ±0.15-second offset allowance. Use the same half-count uncertainty and
eight-subdivision interval calculation for the force required by each GPS
path. Test each path under both clocks. Retain excluded windows and count
their reasons. Reuse the earlier gravity, field and disc settings.

For each model on each flight, select one nonnegative gain using all
training windows and the same [15% allowance](MATCHED_FORCE_GAIN_PLAN.md).
Apply that exact gain to the later windows. Report failures, case counts
and maximum excesses, separately for each model and recording. These are
necessary checks of the scalar acceleration data. They leave uncertain
attitude, shared GPS error, real motion between GPS reports and readings
after calibration unresolved. A pass supplies no model decision.

Use two one-thread workers, one recording per task and a ten-minute
cooperative cap. Charge every target window before testing support. Allow
at most 24 model envelopes with eight subdivisions each per window. The
original limit is 1,123 charged windows and 216,739 total steps, including
one support check per window. Use zero new fit starts, forecast
propagations and GPS position solves. Verify the shared task recovery
qualification and bind at most one technical restart per unfinished task,
two interruptions in total and a 20-minute recovery cap.
