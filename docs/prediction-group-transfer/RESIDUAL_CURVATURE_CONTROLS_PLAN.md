# Test whether residual curvature resolves the coupled solver failures

The [shorter-step test](CURVATURE_RETRY_CONTROLS_RESULT.md) kept the
direction supplied by the Gauss–Newton calculation. Both versions
passed four of eight cases. The hard cases couple a weak coordinate
and a tightly constrained residual along a curved path.

Use the same generated problems and starts to isolate a different
part of the step calculation. The exact half-Hessian of squared
residual cost is the Gauss–Newton matrix plus a sum of residual-weighted
second derivatives. Compare a box-constrained Newton step using the
known analytic matrix with one using finite differences of gradients.
The analytic matrix is available only in these controls. The second
method uses feasible differences within the same parameter box, with
centered differences in the interior and second-order one-sided
differences at the edges. Keep the old solver outcomes sealed and
use their saved dispositions for comparison.

Project the step model to positive curvature and cap each normalized
coordinate change at 0.5. Accept only a real cost reduction that
meets the existing 0.1 agreement ratio. Allow up to eight step
fractions in each backtracking search. Count every residual evaluation,
including each gradient probe, against the original 40-call cap and
reserve two calls for the original fresh-position check. The final gate,
known objective tolerance of 1e-7 and parameter tolerance of 1e-4 are unchanged.

Each method qualifies separately only if all eight controls pass.
Use one worker and one numerical thread, 16 starts, 640 evaluations
at most and a 60-second cooperative limit. Interrupted work uses
the separately qualified recovery allowance. Use no new aircraft
fits or reserved flights. A passing result would settle the
generated comparison and support a separate flight-scale evaluation
of a lower-cost derivative approach. It would not authorize a new
observed fit.
