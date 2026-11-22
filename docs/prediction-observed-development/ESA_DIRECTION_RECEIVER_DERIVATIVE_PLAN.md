# Test the direction result with position and velocity derivatives

Reuse the eight sealed direction windows, both averaging widths, the
recorded later pair angles and the documented antenna-offset replay.
Predict the same force directions using each of the three GNSS-only
exports with two derivative methods. Fit a quadratic to reported
velocity as in the original direction calculation, then independently
differentiate a cubic fit to the same receiver's positions on its
actual timestamps. Keep the receiver time kernels, reference frames,
center coordinates and three matching background-field assumptions.

Compare the resulting 28 later angles with the original measured
angles, separately with and without the antenna offset correction.
The measured angles already contain the raw gyro contribution.
No starting orientation is estimated. First require the primary
receiver's velocity-based prediction to reproduce each original
saved angle and both original sensor scores.

Keep the model ranking, angular RMS separation and change when
switching derivatives or receiver products. Treat the 576 numerical
comparisons as repeated views of eight windows on one development
flight. The receivers share one antenna. The test addresses those
changes in prediction and supplies no absolute error calibration.

Freeze eight tasks with at most 12 receiver-method-width evaluations and
65,280 quadrature points per task. Use one numerical thread and a
150-second limit. Use sealed receiver inputs and public angles. No IMU
replay, calibration fit, original recording read or reserved group.
