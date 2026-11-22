# Check the accelerometer lower bound with one shared gain

Use the previously frozen 991-window packet lower bounds and GPS-predicted
mean force upper bounds. For each recorder and candidate, find the smallest
nonnegative gain correction that clears the lower-bound comparisons on
the training windows under both clocks and all three GPS streams. Hold it
fixed on later windows. Use the existing 15% gain allowance and leave offset
and gravity correction at zero. This is a restricted calibration sensitivity
check, with one gain shared across the axes and all the windows of a recording.

For measured lower bound \(L\), predicted upper bound \(U\) and gain \(g\),
the necessary comparison is \(L/(1+g)\le U\). Take the maximum of
\(0\) and \(L/U-1\) over the training rows. If it exceeds the allowance,
retain a training failure and withhold the later comparison. Report violations
at zero gain and at the fixed training correction. Use all 23,784 saved
candidate cases. No native integrations, optimizers, gyro values or assumed
attitude histories are used.

Passing this comparison leaves continuous force above the packet lower bound,
joint receiver errors, the common timing offset and calibration ambiguity
open. These checks are necessary inequalities under declared assumptions.
They supply no positive model decision or calibrated coverage.

[Matched support](MATCHED_FORCE_SUPPORT_RESULT.md) ·
[Predicted force averages](MATCHED_FORCE_AVERAGE_RESULT.md).
