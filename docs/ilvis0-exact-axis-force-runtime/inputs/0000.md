# Improve the calibration proposals only when the exact gap falls

Start all 32 cases at their [saved training-only calibrations](AXIS_FORCE_PILOT_RESULT.md).
Keep both packet clocks, both GPS paths, both trajectory orders and both
original gain and offset boxes. Keep the same receiver windows and the
same training and later split. Use only the original accelerometer counts
and their half-count intervals. Gravity adjustment stays at zero.

Differentiate the lower and upper packet force norms separately at the
current correction. Choose a trial from a linear program in a bounded
neighborhood. The initial radius is 25% of each parameter's allowed half
range. Check the candidate against the nonlinear training objective.
Accept only a fall greater than 10⁻¹⁰ m/s². Multiply the radius by 1.5
after acceptance, up to 50%, and halve it after rejection. Record both the
proposed and actual gap. Stop on a failed linear step or when the gap is
already within the acceptance tolerance of zero.

Check the first exact objective against the saved pilot and verify the
final objective with its separate packet scoring routine. Save the final
training correction before opening later receiver cases. Score those
cases without changing the correction. Compare all outcomes with the
original one-step proposals.

Allow six charged trials per case, 1,000 linear iterations and two
seconds per trial, with two single-thread workers and a four-minute
cooperative cap. Use zero inertial navigation fits. This is a local method
diagnostic. A residual gap leaves other nonlinear calibrations open.
The comparison uses packet-averaged force and supplies no calibrated
receiver or continuous-force uncertainty.
