# Compare saved timing and calibration solutions

Use the saved pre-boundary-check primary/repeat endpoints for all four currently
unresolved stretches, excluding the already-agreeing pair. The original diagnostic
manifest contains five outstanding complete primary/repeat endpoint pairs;
its untouched-repeat list supplies three additional
repeat endpoints: **eight pairs, sixteen endpoints** in total.

One bounded numerical batch: eight saved pair comparisons and at most sixteen
local nuisance-projection least-squares solves, four numerical threads. Zero
native predictions, observed fits, original-recording reads or changed labels.
Do not rerun a completed or interrupted numerical batch.

For each pair, verify identical receiver epochs, coordinate arrays and parameter
order. Compare actual saved residual differences with each endpoint's first-order
Jacobian prediction. Report time separation, cost difference and largest changes
in normalized calibration coordinates. Project the timing Jacobian onto all
other active columns to describe local timing/calibration dependence.

The projection is an unconstrained linear diagnostic, including columns whose
parameters touch a bound. It is not a replacement fit, global rank gate or proof
that an observed nonlinear optimum is identifiable. First-order extrapolation
between separated endpoints is a test of the local approximation, not a new
prediction of the measurements.

Preserve source/input hashes, original convergence labels and copied evidence.
Use the results to specify a finite matched timing-profile study with nuisance
parameters reoptimized; no observed profile allowance is launched by this review.
