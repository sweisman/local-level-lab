# Diagnose the complete calibration map, not another matrix cut

The joint-rotation relaxation passes its software checks but barely changes
complete widths. Preserve both completed freezes and their unchanged target.

The original 51 coordinates contain 27 physical calibration values and 24
arithmetic error terms. In a real calibration those terms are related functions
of the same physical values; the current necessary region lets them vary more
independently. Matrix inner products constrain only part of that relationship.

## Question

For extreme points admitted by the latest region, keep their 27 physical values
and recompute all 24 error terms from the existing source-bound calibration map.
Does the resulting point still satisfy the training constraints, and how much
does its affine future prediction change? This evaluates a generated calibration
map, not an aircraft trajectory or a new native prediction.

Preserve every original coordinate. Report velocity/clock, lever, acceleration
and force-matrix changes separately, but do not call these percentages of
scientific evidence: their contributions can cancel.

## Finite proposed diagnostic

Use the unique predeclared known-truth sector in each of six candidate/processing
groups from the completed joint-product comparison. For each, propose the six
signed affine extrema, with one-second LP allowances. Independently verify an
exactly feasible witness using the qualified rational repair routine. Its known
generated anchor may help repair the witness only in this explicitly diagnostic
software experiment; it is not available as a prediction method.

Construct the 78-coordinate anchor by lifting the sealed 51-coordinate known
point. Verify it against the current region. Record failed proposals, boundary
collapse and unsupported rounding without replacements. Save the LP proposal,
exact repaired witness and any physical-coordinate conversion before evaluating
the calibration map. No source measurement or failed fit is repaired.

Validate six source-map controls at the known generated physical values against
their sealed common-error values, using the existing 3e-10 component agreement
criterion. Then make at most 36 additional calibration-map evaluations at the
saved witnesses' physical coordinates. Reconstruct complete lifted coordinates
and check every training inequality and box bound with exact arithmetic.

Ceiling: six identities / 36 LP proposals / 42 complete calibration-map evaluations /
250,000 scalar inequality-and-bound checks. Four workers use one thread each;
300 cooperative seconds, no retries or expanded allowance. There are zero new
native predictions, integration bounds, original-aircraft reads or observed fits.
Implementation must charge LP/map/check work before execution and pass focused
accounting, source-binding, rounding and exact-feasibility controls before a new
freeze is launched. This plan itself spends none of that work.

## Interpretation

A physically mapped point violating the necessary training region cannot serve
as a feasible witness for its prediction range. A passing point supplies only
a feasible example for the surrogate calculation; it does not establish a
global optimum, calibrated uncertainty or native trajectory coverage. Report
both outcomes and the changes in every group, with no threshold tuning.

Use the result to choose a properly qualified nonlinear-feasibility or bound-
propagation method. Do not continue a series of small linear-cut variations
without evidence that they address the dominant representation gap. Other
independent roadmap work, including ESA receiver-error qualification, remains
available while observed prediction is gated.
