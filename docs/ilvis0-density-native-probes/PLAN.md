# Nonlinear check of fixed affine calibration proposals

Use only the two specified-field generated inputs, under zero and profiled
removal, from the completed training-density diagnostic. Preserve their broad
27-parameter box, ±1-second clock, 292 training epochs and 438-second prediction.
The reference is the saved zero-expansion trajectory, not aircraft observations
or the separate long-record study's perturbed training truth.

There are twelve identities: two processing assumptions × three future axes ×
two signs. Each makes one LP proposal from the saved physical Jacobians under
the same ±1 m affine training-change constraints. Check its primal feasibility
exactly. Apply one fixed 0.99 contraction, verify the represented point exactly,
and save it before calling the nonlinear model. Never adjust or replace a point
after seeing its outcome.

Evaluate all 293 epochs in one native batch per identity. Preserve its return
status and counter before validation. Check the counter against timestamps at
the actual proposed clock offset. Compare the 292 training positions with the
saved reference using the original coordinate frame. Report the later change
separately; it cannot enter the training-feasibility check.

| Resource | Per identity | Total maximum |
|---|---:|---:|
| LP proposals | 1 | 12 |
| Exact primal checks | 2 | 24 |
| Native batches | 1 | 12 |
| Queried epochs | 293 | 3,516 |
| Conservatively charged packet visits | 28,128,000 | 337,536,000 |

Use one numerical worker/thread with other active allocations reserved. Each
LP has a five-second limit; cooperative study ceiling is 600 seconds. No
interval bounds, aircraft reads, observed model fits, retries, process signals
or allowance increases. Freeze sources, environment, compiler, saved baselines
and verified hash references to existing frozen generated inputs before launch.

A numerical pass means the diagnostic ran correctly. Nonlinear training
feasibility is a separate outcome. Large feasible later changes would demonstrate
ambiguity in this generated test. Rejected sampled points do not prove unique
prediction or justify dropping unexamined regions. Neither result qualifies an
aircraft error law, nonlinear uncertainty coverage or scientific significance.
Publication uses sealed results only.
