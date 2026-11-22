# Check how fast the recorded accelerometer force must change

Use the two added NASA recordings and their original whole packets. The
[packet averaging bound](GYRO_FREE_CALIBRATION_CONTROLS_PLAN.md) needs an
upper limit on body-frame force change. Adjacent packet averages provide
a way to test whether a proposed upper limit is too small. They supply
no upper limit by themselves.

If continuous force changes at most \(L\) m/s³, the difference vector
between two consecutive mean forces has magnitude at most \(L\) times
the separation of their interval midpoints. For each pair, subtract the
half-count limit and a per-axis packet error allowance from the observed
difference before dividing by that separation. A constant accelerometer
bias cancels. Allow each gain correction up to the stated 15% magnitude
and use the least change consistent with that scale range. Evaluate
per-axis extra allowances of 0, 0.02, 0.1 and 0.5 m/s² without choosing
one as the measured noise level.

Report the median, 95th percentile and maximum lower bounds for both
clock assumptions. A pair stays on one side of the training cut only
when its complete support, including the existing ±0.15-second timing
allowance, ends by the last earlier receiver report or starts at the
first later report. Report counts for both sides and the full prepared stretch.
Use accelerometer integers and packet times only. This checks a necessary
condition for a continuous-motion model and leaves sensor filtering,
signal errors and unobserved between-packet changes open.

Use one task per recording and two single-thread workers, with a
two-minute cap. Charge one pass per clock and extra-error allowance and
at most one step per adjacent pair in each pass. Use no new fits,
forecasts or receiver solves. Bind the existing task recovery qualification
with one technical restart per unfinished task, at most two interruptions
and three minutes for recovery. The two stretches contain 224,556 pairs,
so the 16 passes allow 1,796,448 pair checks.
