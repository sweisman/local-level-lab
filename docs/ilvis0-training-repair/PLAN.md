# One fixed repair of original-observation probes

Use the four previously saved scale-1/10 generated probes: positive and negative
north directions under zero and profiled removal. Preserve the original nonzero
truth, all five perturbed training observations, 96000 packets, 27 physical bounds,
±1-second clock and 20/20/50 m future width targets. Earlier failures stay unchanged.

For each saved point, use its existing native Jacobian in one minimum-norm linear
solve. Fifteen rows target the known generated truth at the five earlier epochs;
one additional row preserves that seed's computed future north prediction.
No future observation enters the solve. This constructs a counterexample probe,
not an honest held-out prediction or a confidence interval.

Use all 27 columns, SVD rcond 1e-12, maximum normalized correction 0.25 and maximum
linear row mismatch 0.001 m. Reject out-of-box points without clipping. These are
proposal checks; only a new nonlinear evaluation against the actual unchanged
training observations can establish training feasibility within ±1 m per axis.

Save each proposal before querying it. One new native batch per valid proposal
returns five earlier predictions and the 438-second prediction. Preserve failures
and report sampled spreads including the original truth. Small spreads are not
outer bounds; a feasible spread above a width target would disprove that target
for this generated observation problem only.

| Resource | Maximum |
|---|---:|
| Fixed identities / linear solves | 4 / 4 |
| New native batches / queried epochs | 4 / 24 |
| Conservative reserved packet visits | 2,304,000 |
| Numerical threads / reserved elsewhere | 1 / 2 |
| Cooperative wall ceiling | 600 seconds |

Freeze source, input references, environment and compiler before launch. No
iterated repairs, alternate scales, retries, signals, observed aircraft fits,
original-data reads or allowance increases. This does not change the running
long-history study, qualify native execution error or establish an aircraft
error law. Existing scientific results remain unchanged.
