# Tighten ESA calibration bounds by linking terms during the search

Reuse the eleven surviving physical calibration boxes from the
[joint floor check](ESA_LINKED_FLOOR_SUPPORT_RESULT.md). Preserve the
25.41-unit forecast separation, the earlier squared-loss limit of 0.01,
all 60 coordinate columns, and the previous cover, exclusions and witnesses.
Use only the saved affine trajectory and the original linked static map.

For each child, seek a large signed forecast change in the lifted linear
program. Compare its shared terms to the terms produced by the same physical
calibration. Try three directions for bounding this discrepancy. Use the
shared-coordinate discrepancy itself, its projection through the earlier
residual design, and its contribution to the forecast score. Center each
direction using the linked map's derivative at the proposed physical point.
Bound that entire linear expression over the child with the outward interval
map. Add a cut only if its exact affine slack excludes the proposed point.
Add an earlier residual projection if that proposal also exceeds the earlier
norm limit. The previous linear rows and coordinate boxes stay in force.

Check the resulting forecast bounds with the existing exact dual verifier.
Neither a reported solver optimum nor an infeasible status proves a bound.
Check every result against the saved witnesses. Keep the earlier bound unless
a smaller bound is verified. Require a positive remaining separation to claim
a gap under this approximation. The full integration remainder and the
aircraft prediction-error law need separate evidence.

Freeze six linear proposals and at most fifteen graph cut checks per child,
with two one-thread workers and a 300-second cooperative limit. Test a nonlinear
map whose lifted variables would otherwise erase a known gap. Test that the
bound keeps the true graph in the search region. Bind the existing qualified
recovery policy with a separate 600-second recovery allowance. Run no new
trajectory integrations, inertial fits or confirmation-flight analyses.
