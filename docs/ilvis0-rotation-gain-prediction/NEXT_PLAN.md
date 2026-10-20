# Diagnose the remaining relaxed-region width

The last two saved comparisons passed correctness but missed the fixed
usefulness target. Before adding constraints or recomputing native bounds,
check whether the retained linear relaxation itself admits wide predictions.
This is a post-prediction mathematical diagnostic, not another prediction result.

First qualify exact feasible-point verification and repair. A floating LP proposes
a point. Verify every box and inequality with rational arithmetic. If needed,
mix the proposal toward a supplied exactly feasible anchor, using the largest
exact mixing fraction required by any violated constraint. An anchor on a
boundary may force complete replacement; preserve that loss of usefulness.
An invalid anchor or unsupported calculation must be reported, never repaired
silently. Keep all 51 columns. Known-answer tests must cover strict and boundary
anchors, point boxes, violated bounds, contradictory rows, gain signs and exact
objective evaluation. No optimizer status substitutes for exact feasibility.

Then freeze six saved identities: the unique known-truth sector of each existing
generated model/processing case. This choice uses the already declared synthetic
truth and is only for diagnosis after all predictions are sealed. It is not an
aircraft selection rule or a new independently validated cohort. Use the saved
known calibration/error vector as the anchor only after exact verification.

Allow six LP proposals per identity, one in each signed future-coordinate
direction: 36 proposals total, each at most one cooperative second. Preserve
proposals, exact repair fractions, rational feasible witnesses, objective values
and all constraint checks. Four workers use one thread each with a 180-second
cooperative allowance. Zero native calls, bounds, originals, observed fits,
retries or protected outcomes. Freeze identities, sources, inputs and environment
before execution; software controls must pass first.

Report witness-supported lower bounds and existing certified upper bounds on
the relaxed affine width, separately from the retained unshared allowance and
the complete union across sectors. Compare them with the unchanged target.
Feasible relaxed witnesses are not evidence that those calibrations or error
vectors are physically realizable. A demonstrated relaxation floor limits what
better dual optimization can achieve; it does not measure aircraft uncertainty
or prohibit a genuinely stronger physical propagation method.

Publish unsupported anchors and uninformative repairs without replacements.
The result guides the next derivation; it does not clear the gate for longer
or observed predictions.
