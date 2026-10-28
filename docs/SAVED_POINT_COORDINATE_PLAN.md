# Full saved-point check of compensated coordinates

The [small coordinate controls](coordinate-precision-controls/INTERPRETATION.md)
qualify compensated accumulation on six known-answer fixtures and retain the
three-model compatibility checks. The next question is whether that arithmetic
resolves derivative and stopping discrepancies in the same four exposed
development examples.

## Fixed work

Reconstruct the original inputs and error operator once per saved point. First
evaluate the unchanged original implementation and require its baseline cost,
parameter order and input hashes to reproduce exactly. Then switch only the
diagnostic native provider to compensated coordinates with the qualified inward
timing branch. Preserve the physical equations, bounds, error operator and
original numerical environment.

For the compensated calculation:

1. Repeat the residual and complete Jacobian three times.
2. Compare **every** retained parameter column with feasible finite differences
   at the original normalized steps of 0.001, 0.0001 and 0.00001.
3. Repeat the original undamped stopping probe once, using its original cost,
   stationarity and position limits. Record the signed actual and predicted
   cost changes and the parameter step.

The earlier matched diagnostic already isolated the timing effect. This phase
checks the complete derivative matrix and stopping calculation together rather
than reconstructing the same error operator for several narrower follow-ups.

## Finite allowance

Four tasks, one per exposed point. Each permits one baseline evaluation plus
at most 170 compensated residual/Jacobian evaluations: **171 per point, 684
overall**. The complete planned probes need 650 evaluations if all finish.

The reconstruction cap is 23,634 single-packet operations per point. Including
full evaluations, each task permits at most **23,805 native calls and
318,228,129 conservatively counted packet-query visits**. Overall caps are
95,220 calls and 1,272,912,516 visits. Prepay separately; unused work remains
charged. Do not reuse an earlier phase's allowance.

Use **four workers with one numerical thread each**, zero reserved threads
only after other numerical work finishes, and a one-hour cooperative ceiling.
Allow at most three compiler builds per worker: the original noise bridge,
original wider tangent and compensated tangent. No retries or deadline signals.

## Implementation and gate

Extend the existing saved-point study and reporting components with an explicit
compensated/full-check configuration. Reuse their original reconstruction and
source-bound probe substitution; do not copy another worker. Qualify the new
configuration, complete-column probe, accounting and reporting before preparing
its source/environment/input freeze.

Keep every failed original label. A passing new stopping diagnostic is not a
new fitted optimum or a relabeling of the old result. No optimizer runs,
forecasts against new observations, new noise families, aircraft reads or
protected observations are included.

Publish all outcomes, including remaining disagreements. A failed comparison
blocks dependent fitting. A passing comparison allows a separately frozen
solver qualification; it does not restart calibration or establish a confidence
threshold. The 53-stretch findings remain unchanged.

[Roadmap](ANALYSIS_ROADMAP.md) · [Next analyses](NEXT_STEPS.md).
