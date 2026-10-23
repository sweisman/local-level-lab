# Qualify feasible steps before more trajectory searches

The completed searches do not settle the ambiguity question. Eleven directions
found no new training-compatible point; the remaining direction found one.
Every search exhausted its fixed allowance. Preserve all twelve outcomes and
do not restart them.

The saved first proposed steps already predicted 1.43–67.20 m training errors
in the local linear calculation, against the 1 m limit. Actual errors were
393.64–1,740.07 m. These were large moves through a nonlinear problem, rather
than useful tests of nearby feasible alternatives. Initial batched values and
Jacobians match the saved parent in all twelve cases; that consistency check
does not independently prove derivative accuracy.

The next component should:

1. Construct a local proposal that explicitly satisfies the linearized training
   inequalities and original calibration bounds. Check the represented proposal
   with exact arithmetic before spending a native evaluation.
2. Limit the proposed step with a declared trust radius. Reject or shrink a bad
   proposal; do not narrow the physical parameter domain or discard columns.
3. Check actual nonlinear training compatibility after every evaluated move.
   Preserve rejected moves and charges, and retain the best feasible point.
4. Pass independent controls with recording-like derivative scales, narrow
   feasible valleys, known alternatives, inactive columns and boundary solutions.
   Small well-scaled examples alone were insufficient for the last method.
5. Use the earlier accepted probes as positive controls. The known 13.33 m
   north spread cannot disappear merely because a new optimizer misses it.

Keep all 27 physical coordinates, original observations, clock assumptions and
width targets unchanged. Shared study code should handle lifecycle, charging
and publication. Only after software qualification should a separate finite
full-history comparison be frozen. This plan creates no retry allowance for
the completed search and qualifies no aircraft prediction fits.

[Completed search](README.md) · [Earlier accepted probes](../ilvis0-truth-probes/INTERPRETATION.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
