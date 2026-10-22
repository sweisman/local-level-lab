# Test the linear calibration choices in the nonlinear model

Use the two specified-field generated cases, with and without profiled removal,
from the completed density diagnostic. Keep their original broad physical box,
±1-second clock, 292 training epochs and 438-second prediction.

Predeclare twelve identities: two processing assumptions × three future axes ×
positive/negative direction. For each, make one training-constrained LP proposal
using the saved physical Jacobians. Check its primal feasibility exactly.
Convert the proposed calibration to a fixed 0.99 contraction before examining
native outcomes; verify that represented point exactly as well. Save it before
calling the native model. No adjustment or replacement may follow an outcome.

Evaluate all 293 epochs at that calibration in one native batch. Compare the
292 earlier positions with the saved zero-expansion outputs, under the same
±1 m coordinate-change constraint. Separately report the later displacement.
Preserve every rejected point and native failure. A linear-feasible point is
not automatically nonlinear-feasible; neither kind is a fitted aircraft result.

Proposed ceiling: twelve identities, twelve LP proposals, twelve native batches,
3,516 queried epochs and 337,536,000 conservatively charged packet visits.
Each LP has a five-second limit; total cooperative ceiling is 600 seconds.
Use one numerical worker/thread with other active allocations reserved.
No interval bounds, aircraft reads, observed model fits, retries, process signals
or allowance changes. Test and freeze the adapter, source/input hashes, environment
and separate accounting before launch. Publish from sealed results only.

This is a diagnostic of the relaxation. It cannot qualify whole-period nonlinear
coverage, the aircraft error law or independent scientific significance.
