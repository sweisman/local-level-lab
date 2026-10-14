# Paired qualification of wider-arithmetic fitting

The [precision diagnostic](../ilvis0-shared-leg-precision-20261014/README.md)
passed the unchanged full probe checks at five of six saved endpoints with wider
arithmetic. Both cost-only failures passed; the separate vertical-stability failure
did not. This trial tests numerical recovery in that predeclared failure class.

## Recordings and selection

The two targets are the IMU8 recording on 24 October 2009 and the DMS recording
on 7 October 2015. Each shares a receiver track with a completed counterpart.
They are selected by their frozen relative-cost-only stopping failures, not by
which scientific model has the smallest cost. The September disc position failure
requires a different numerical investigation and is outside this trial.

Each target retains its entire original qualifying stretch and receives all three
models under both processing cases. These are permanently mounted survey IMUs;
no passenger reversals are fabricated. Group-1 fused navigation remains context,
not an Earth-model observation. Common-time recorder differences remain descriptive
checks, rather than pooled or substituted measurements.

## Finite allowance

- Twelve primary fits: six per target, at most 40 native fitting evaluations each.
- Two matched completed-recorder controls: one per pair, at most 40 evaluations each.
- Two repeated starts of the previously failing model/case: at most 200 evaluations
  each, using the same frozen seed plus the original deterministic 0.01 perturbation.
- Two diagnostic predictions per start.

This is **16 starts and 992 native sweeps maximum**, with **no retries**. Four
numerical threads are the total allocation. At measured wider-arithmetic speed,
the ceiling is approximately **7–9 hours**; early stopping can substantially reduce it.
This is a separate freeze, never a use of any completed study's unused allowance.

## What changes and what stays fixed

Use the qualified diagnostic kernel with 64-bit internal mantissas rather than
53-bit mantissas. The existing actual-position solver, physical equations, raw
increments, receiver observations, covariance, clock branches, calibration bounds
and stopping tolerances remain unchanged. Latest frozen primary endpoints are
the seeds, without choosing a lower-cost repeat. Every attempt is charged before
execution. Interrupted attempts cannot retry; only unstarted identities may continue.

## Qualification and reporting

Both controls must converge and agree with their saved cost within 1e-6 relative
and their predicted track within 1 cm RMS per axis. Each target needs all six primary
fits and its repeat to converge. Repeat cost and predicted tracks must agree within
1e-6 relative and 1 cm RMS per axis. A failed repeat cannot replace a primary.

Report individual numerical failures and keep original dispositions alongside new
evidence. Interpret globe versus the specified disc before the background-field
comparison. Even a fully qualified numerical comparison remains an uncalibrated
model preference; this trial cannot identify the field's physical cause or resolve
solar versus sidereal rate. No broad recovery rollout follows unless this narrower
numerical qualification succeeds.
