# Score the turn and the other second-leg cells on the common clock

Use the four [whole-second cells with sealed receiver inputs](ESA_DIRECTION_HOLDOUT_CLOCK_RESULT.md).
On each, read the original iMAR rates and specific force once, using the
same 50 ms edge padding, 5 ms gap ceiling and trapezoidal construction
as the earlier angle check. Verify the original file hash and require
all eight late direction supports to be covered by its original samples.
Compute the measured pair angles at both widths, leaving the antenna
offset unchanged. Apply one set of measured angles to the three receiver
exports and both shapes. Preserve the original half-second comparisons.

Use exactly the prior two differentiation methods, three field endpoints
and continuous retention interval with the 81-point grid and its analytic
bound. Reproduce the sealed primary endpoints. Use the actual alternate
sample times in differentiation and the common primary receiver kernel
in all predictions. Report continuous score intervals, shifts from the
primary endpoints, and the earlier absolute error references. Compare
the zero-field turn result separately across the three exports and to
the original half-second check. Any overlap leaves the preference
unresolved for that setting. Retain failed clock or support checks and
all scored windows.

This comparison tests the receiver processing effect and a half-second
shift within four previously selected flight cells. All three receivers
share one antenna. The error common to the receiver exports and independent
flight adequacy remain open.

Freeze one task with one permitted read of the original IMU file to verify
its byte count and hash, four bounded inertial slices of at most 121,000
original sample intervals, and 24 charged receiver/width operations under
the same quadrature limits as the original field-range check. Write and
hash each window result as it finishes. Use one numerical thread and a
180-second ceiling. Use only the sealed receiver rows and the four iMAR
slices from development recording 187. Run no fits and keep the seven
reserved flight groups unopened.
