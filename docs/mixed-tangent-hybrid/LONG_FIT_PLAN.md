# Long-record paired fitting gate

## Question

Does the selective-precision tangent preserve the training objective and
withheld positions of the existing wide-precision tangent when the full
training and prediction procedure uses twenty minutes of generated data?

## Frozen design

Use the same deterministic generated IMU and receiver protocol as the
[completed short-fit study](paired-qualification/README.md). Extend each
record to 1,200 seconds at 300 Hz and use 1,199 one-second receiver epochs.
The six cases remain three physical candidates by two processing settings,
at latitude 55°, one fixed start per case. Each pair changes only tangent
arithmetic. It shares the generated measurements, initial values, optimizer,
calibration bounds, training split, withheld truth, and prediction times.

Each fit permits at most 200 tangent evaluations. Across six cases the
allowance is at most 2,412 native calls, 464,550,348,000 packet/query visits,
4,320,000 constructed intervals, and 4,343,988 generated samples. Use four
workers with one numerical thread each, at most six hours of wall time, no
retries and no observed or protected recordings. Charge work before execution.
Keep sealed completed cases after an interruption; any unfinished attempt
remains charged under the frozen recovery rules.

Before launch, qualify the longer recipe, source closure, environment,
input hashes, finite charges and independent score replay. Require the
completed twenty-minute kernel check and the completed short paired-fit
check as parents. A case passes only if both fits independently converge,
retain all nuisance columns, meet the existing physical prediction screen,
and differ by at most 0.01 m at every withheld three-dimensional position.
Report training-cost and position differences even when a case fails.

This is a software substitution gate, not an Earth-model comparison. A pass
may support replacing the wide tangent only after measuring whole-fit CPU
time and checking observed-data source bindings separately. It does not
calibrate aircraft prediction errors or statistical decisions.

The first release of this plan stopped before any task was charged: its
frozen worker adapter used a package-relative import that fails when loaded
directly from the source snapshot. That terminal record is retained. The
second release changes only the adapter import and adds a direct-load test;
it retains this scientific design and all finite limits.
