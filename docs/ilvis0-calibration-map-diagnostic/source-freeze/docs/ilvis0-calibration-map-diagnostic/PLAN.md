# Can one calibration produce the allowed extreme errors?

This diagnostic tests generated software cases, not aircraft data. Earlier
linear constraints barely narrowed prediction ranges. The question is whether
their extreme error combinations can come from one physical calibration.

## Selection and limits

Use the unique, already declared known-truth sector in each of the six groups
from the completed joint-product prediction comparison. Preserve its full
78-coordinate region, contracted bounds, coefficients and input packets.
The 27 physical values and 24 original common-error terms remain separate from
the 27 arithmetic products.

Freeze six identities. Each permits six one-second LP proposals, seven complete
calibration-map evaluations and 41,000 scalar checks: **36 proposals, 42 maps and
246,000 checks total**, within the earlier 250,000-check ceiling. Four workers
use one numerical thread each. The cooperative wall allowance is 300 seconds.
Zero new native predictions, native integration bounds, original-aircraft reads,
observed fits or retries. Interrupted work remains charged. Completed work cannot
restart or transfer unused allowance.

Scalar checks count every exported training-inequality and box-bound evaluation,
including the three checks inside rational witness repair and the separate
independent verification. They also include exact/rounded physical-domain checks
and the known-anchor component comparison. The source map's own input validation
is part of its separately reserved map call, not an extra exported-region check.
LP-internal work is limited by its one-second proposal allowance.

## Procedure

1. Verify hashes, environment, complete reference report and source identities.
2. Lift the sealed known generated anchor and verify exact feasibility. Recompute
   its 24 common-error components and require agreement within the existing
   3e-10 tolerance. This anchor is diagnostic truth, not a prediction input.
3. Propose positive and negative affine extrema on all three future axes. Save
   each raw proposal, repair it toward the known anchor with exact arithmetic,
   then independently verify every inequality and bound.
4. Save the exact witness and binary conversion of its 27 physical coordinates
   before evaluating the source map. Reject unsupported conversions; never clip.
5. Recompute all 24 common errors. Evaluate all arithmetic products even if the
   resulting point falls outside the relaxed box, so violations remain visible.
   Check the complete mapped point with independent exact arithmetic.
6. Report training feasibility, boundary collapse, rounding, and signed changes
   from the physical, velocity/clock, lever, acceleration and matrix blocks.
   Keep cancellations visible. Unsupported proposals have no replacements.

Every LP, map and scalar-check batch is durably reserved before execution.
Publication reconciles cumulative reservations against sealed results. This is
an audit of recorded reservations, not an independent observer of all CPU work.

## What the result can establish

A mapped point outside the necessary training region cannot justify an attainable
prediction extreme. A passing point is only one feasible example in the surrogate
calculation. Neither outcome establishes a global physical optimum, a native
trajectory, calibrated uncertainty, or a scientific model preference. The 53
aircraft results and protected ESA confirmation groups remain unchanged.

Choose the next nonlinear-feasibility or propagation method from these results;
do not launch another minor matrix-cut variant by default.
