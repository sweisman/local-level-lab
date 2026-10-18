# Scaled affine correction qualification and matched trial

The [saved correction audit](../ilvis0-correction-audit-20261018/INTERPRETATION.md)
reproduces the failed right-side step using the saved center Jacobian. The old
bounded solver reports success but returns a higher affine cost than the feasible
zero correction. This is a numerical failure before nonlinear propagation.

## Candidate

`lll.ilvis0_scaled_branch` reparameterizes each affine correction coordinate by
its available range before applying the existing bounded-variable least-squares
method. Every column and original physical bound remains present. The mapped
solution must be feasible, no worse than a known feasible reference, and meet
a range-scaled affine stationarity check. The outer native stationarity, cost,
position, continuity and source-to-final checks remain unchanged. Neither fixed
timing nor a damped zero step is substituted for the full problem.

The local affine check uses at most 100 iterations and tolerance 10^-10.
Its additional stationarity check uses 10^-8 and projects bounds within 10^-6
of each coordinate's allowed range. This qualifies the affine solve only; it
does not replace the native 10^-4 stationarity or any physical-position limit.
All candidate modules are private copies; frozen dependencies remain unchanged.

## Software qualification

One 33-test batch, 120-second ceiling: all 21 existing representable-clock/native
motion controls applied to the new candidate, nine additional affine controls
and three worker/scope checks. The affine controls include known bounded optima,
rank deficiency and both exact saved failed systems. At most 1,024 callback/native
software calls, 81 compiled-motion calls and six clock comparisons. No originals
or observed native calls are permitted during software qualification.

Only a complete qualification pass permits observed preparation. Freeze the
qualified sources, input hashes, native kernel, environment, task identities
and this plan before launch. Preserve unsuccessful exploratory solver tests;
the final candidate retains BVLS with coordinate rescaling rather than changing
both parameterization and solver family.

## Observed limits and acceptance

Scope remains only `370cec66878c4c1cf84b4ceb`, profiled-removal specified-field
globe, complete original primary and repeat, plus two fresh smooth controls.
Two controls × three calls and two target checks × 26 calls: **four charged
identities, 58 native evaluations, zero optimizer starts**. Maximum 402,048 clock
queries, six bounded affine solves, four total numerical threads, no retries.

The corrected, already qualified receiver-context adapter remains unchanged.
Do not alter intervals, clocks, measurements, covariance, physical bounds or
processing assumptions. The two completed earlier trials remain frozen, including
their errors, failures, charges and unused allowances.

Require controls first, full two-sided native gates, source reproduction and
cumulative source-to-final stability. Require relative pair cost difference
at most 10^-6 and per-axis track RMS at most 0.01 m. Preserve every failed start
and charge before calling native code. A pending transaction blocks continuation;
completed or charged identities cannot restart.

Even a pass needs a separate saved review of all six primaries, both required
case repeat pairs and controls. No production promotion, significance claim or
change to **51 globe / 0 flat / 2 unresolved** follows from qualification alone.
