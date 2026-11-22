# Check the full range of forecast-error scales

Use the eight saved windows and both inertial error descriptions from the
[original matched study](ESA_COMPONENT_SCALE_TRANSFER_RESULT.md). Preserve
that study and the [whitening result](ESA_WHITENED_SCALE_TRANSFER_RESULT.md).
The question is whether any common set of the three allowed variance
multipliers can put every window inside the original descriptive Gaussian
reference. This is a retrospective compatibility test. A passing set
would still need a prediction test on unused data.

In native-whitened coordinates, divide each added variance by native
variance. The two log ratios range from −10 to 10. For fixed ratios the
quadratic score is the whitened quadratic divided by native variance.
The whitened quadratic decreases as either added-to-native ratio
increases because both added covariance terms are positive semidefinite.
At any ratio rectangle, bracket each score by its two diagonal corners.
Intersect the resulting interval for native variance across the eight
windows and with the original absolute variance bounds `[exp(−5),
exp(5)]`. Exclude a rectangle only if that intersection is empty.

Process the largest log-ratio rectangles first, bisecting the widest
side. Check the midpoint for a feasible witness and verify any witness
against all eight original metre-coordinate scores. Reserve up to 256
boxes per error description, one task per description, one numerical
thread and a 120-second cooperative cap. Record every excluded or open
rectangle and the reason for completion. Return unresolved if the
remaining boxes do not fit inside the allowance. Start no optimizer
or inertial fit and read no reserved flight.

Before running, verify the quadratic brackets on analytically tractable
positive-semidefinite cases, including zero components, an interval that
only touches a boundary, a known feasible case and a known incompatible
case. Use a checked solve residual to widen computed endpoint bounds
and retain floating-point margins. Describe any result as a numerical
compatibility check under the working reference and the frozen box.
