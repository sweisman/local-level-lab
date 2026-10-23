# Test controlled steps before another prediction search

This software trial asks whether a small proposed change in calibration can
preserve the earlier position observations while changing a later prediction.
It uses generated inertial measurement unit (IMU) data only. It reads no aircraft
recording and changes none of the 53-stretch findings.

The previous nonlinear search mostly proposed moves that already violated the
training limits in its linear approximation. The replacement explicitly checks
that approximation before spending a native integration, then checks the actual
nonlinear result. A local step limit controls the search, not the physical domain.

## Fixed comparison

- Reuse the six original generated cases: three physical models under zero and
  profiled upstream removal. Preserve their 96,000 packets, five earlier receiver
  epochs at 2, 10, 30, 180 and 290 seconds, and future epoch at 438 seconds.
- Keep all 27 physical calibration coordinates, original bounds, observations,
  clocks and 1 m training allowances. Retain the existing 0.00001 m numerical
  guard as an assumption; this trial does not independently qualify that guard.
- Test both northward prediction directions at each of three normalized step
  radii: 0.001, 0.0005 and 0.00025. This gives **36 fixed identities**.
- At each identity, first maximize local predicted progress, then minimize the
  largest normalized training residual while preserving at least 98% of that
  progress. Both linear programs keep every physical column. Record solver
  failures and exact primal checks; make no global-optimum claim.
- Check each represented proposal with exact arithmetic. Use a 0.01 m search
  margin and the declared radius. A failed or non-improving proposal consumes
  no new native integration and remains a recorded rejection.
- For a checked improving proposal, evaluate all six epochs in one native batch.
  Preserve raw output before interpretation. A usable step needs actual training
  compatibility with at least 0.02 m margin, signed progress above 0.000001 m,
  and actual/predicted progress ratio at least 0.1.

## Finite allowance

The shared study runner freezes sources, inputs and numerical environment before
launch. It permits four workers with one numerical thread each, **600 seconds
total**, with a cooperative 120-second check per identity. No process is killed
to enforce a clock. Each linear program has a one-second cooperative solver limit.
Individual native calls must finish; the clock allowance is not a termination signal.

Across the study, reserve at most:

| Work | Maximum |
|---|---:|
| Task starts | 36 |
| Linear programs | 72 |
| Exact proposal checks | 288 |
| Native batches | 36 |
| Conservative packet visits | 20,736,000 |
| Nonlinear candidate audits | 36 |
| Optimizer searches or aircraft fits | 0 |

Reserve two linear programs and eight exact checks before each proposal; charge
each native batch and its 576,000 conservative visits before execution. Record
all three radii, including failures. No retries, replacement identities or budget
expansion. Independent unit controls cover narrow nonlinear valleys, inactive
columns, physical boundaries and recording-scale derivatives.

Earlier accepted probes are positive controls. Recheck all six accepted and six
rejected labels from saved outputs under their original criterion. Preserve their
13.33 m and 5.90 m north spreads; failure to rediscover them is not zero uncertainty.
Rechecking saved positive controls performs no new native evaluations.

## Qualification and continuation

All 36 identities must finish with valid records, and every model/processing/
direction combination must have at least one usable radius. A rejected radius
is not an execution failure; it is evidence about the local step limit.

Passing qualifies only this first-step component. It does not qualify a complete
search, an outer prediction range, a calibrated uncertainty interval or real-flight
adequacy. A subsequent full-history search needs a separate finite freeze and
must preserve the earlier accepted alternatives. V01 remains unqualified and
dependent observed prediction fits remain blocked.

Reporting recomputes acceptance from sealed saved values, checks source/input
hashes and publishes every outcome. The shared archive preserves frozen source,
input and output bytes without retaining duplicate loose trees. Completed work
must not be relaunched.
