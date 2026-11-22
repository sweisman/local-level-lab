# Compare receiver-derived force across the eleven matched survey legs

The [exact calibration study](EXACT_AXIS_FORCE_RESULT.md) leaves force gaps
on two pilot recordings. Test how much choice of receiver can affect the
same kind of force calculation across the
[eleven sealed receiver pairs](../ilvis0-receiver-window-pairs/README.md).
This comparison uses receiver measurements alone and does not choose
new targets from model residuals.

Keep all 490 saved target dispositions. Calculate on the original
30-second window only where both receivers accepted that width. Restrict
each fit to the same exact GPS epochs in the two streams, require at least
five matched epochs bracketing the target, and reject a gap above 1.5 s,
including support at either end. Retain every unsupported target. Use the
same quadratic and fourth-degree fits as the pilot. Compare the two
receivers' north, east and vertical accelerations at the centre and the
eight-node mean force magnitudes over the full 30 seconds. Use the
standard globe coordinate conversion to express centre accelerations in
north/east/up. Evaluate all
four shape and field candidates with the same gravity.

Summarize each receiver pair separately. Compare the size of its force
differences with the remaining calibration gaps on the two original pilots.
The comparison measures how far the predictions move when using a different
receiver. Shared satellite errors can cancel, and physically different
antenna positions can add real motion. These differences do not establish a
distribution for the absolute error of either receiver.

Use at most 490 matched windows, two receivers, two orders, four models
and eight quadrature evaluations per case. The ceilings are 62,720 force
quadrature evaluations and 1,960 centre kinematic evaluations. Use one
numerical thread and zero inertial fits or receiver
position solves.
Freeze the pair identities, input hashes and source before calculation.
