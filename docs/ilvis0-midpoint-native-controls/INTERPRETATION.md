# Skipping the unused certificate preserves all checked results

**All 24 known-answer cases passed. Every one of the 348 bound reports matches
the predecessor exactly**, including the predicted center, coefficient maps,
physical domains, source bindings and all four error-allowance arrays.

The qualification took 142.93 seconds and used its fixed 78 native comparisons.
The matrix retains all three physical candidates, both processing cases,
stationary-pose, derivative and nonlinear-containment checks. The 12 focused
source checks and seven native checks also pass.

The change avoids calculating an unused endpoint force certificate. It retains
the endpoint rotation state needed by the next packet and the midpoint
certificate actually used by the integrator. No calibration assumption,
prediction-width target or recorded aircraft measurement changed.

This qualifies equivalence on the tested software matrix, not a speedup. A
[separate matched runtime study](../ilvis0-midpoint-runtime/PLAN.md) runs both
implementations on the six original complete child domains, with fixed limits
and balanced order. It subsequently [failed](../ilvis0-midpoint-runtime/INTERPRETATION.md):
only two pairs completed. No replacement future-bound rollout follows.

The full prediction-width gate still passes in four of six cases. Useful
recording-scale bounds and the observation-error model remain unfinished.
No new aircraft fit or statistical claim follows from these controls.

[Verified result and accounting](README.md) · [Frozen scope](PLAN.md) ·
[Remaining width](../ilvis0-east-width-audit/INTERPRETATION.md).
