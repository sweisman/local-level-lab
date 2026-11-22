# Estimate curvature from tangent changes in weak directions

The [strong-residual correction](STRONG_RESIDUAL_RESTORE_RESULT.md)
passed all eight generated controls with analytic curvature. Its
full gradient-difference estimate passed six. The two remaining
starts used all 40 allowed evaluations.

Use the current tangent to identify directions below one thousandth
of its largest singular value. When both weak and strong directions
are present, estimate how the tangent changes along each weak
direction with two feasible probes at the existing difference scale.
Multiply the tangent difference by the residual at the current point.
This estimates the part of the cost Hessian missing from Gauss–Newton
without differencing two full gradients. Keep the weak and cross
curvature terms, and use Gauss–Newton for the strong-to-strong terms.
If a probe is infeasible or the tangent has no useful split, keep the
existing coordinate-wise gradient differences. Charge all probes.

Keep the same direct residual change, trial restoration, box, step
radius and fresh gate. Use the exact same eight generated cases and
starts as the previous estimated-curvature arm, with up to 40
evaluations each. Compare to the saved analytic and estimated results
without rerunning them. Require eight passes and actual use of the
weak-direction estimate before qualifying for a separate generated
flight test.

Total allowance is eight starts, 320 residual evaluations, one
worker, one numerical thread and 60 seconds. The usual finite
interruption recovery allowance is bound to the freeze. There are
no aircraft fits, source measurements or reserved-flight reads.
