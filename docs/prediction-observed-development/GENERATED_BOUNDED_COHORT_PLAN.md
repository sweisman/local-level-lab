# Finite generated full-path and calibration cohort

## Question and frozen cases

Do the two technical pilot's broad interval widths, inaccurate fitted paths
and imperfect sensor-calibration recovery recur in fresh known-answer cases?
This is development evidence, not an aircraft uncertainty calibration.

Reuse the exact 300 Hz, 900-second route, 600 training and 300 later receiver
epochs, rotating-globe truth, positive interior sensor case, one starting
point, 26 fitted nuisance directions, bounds, clocks, covariance assumptions
and 200-evaluation limit of the closed bound-aware pilot. Keep its increment
and point error laws. Use **four fresh independent seeds per law**:

| Law | Seeds |
|---|---|
| Increment | 630101, 630102, 630103, 630104 |
| Point | 630201, 630202, 630203, 630204 |

The short technical preflight uses increment seed **630000**, 10 seconds,
nine receiver queries and eight fit evaluations. It has a separate identity.

## Execution and gates

Each task prepays the existing finite base allowance plus exactly one extra
complete error-operator pass. No retries, changed seed, expanded ceiling or
new source are permitted within a frozen task. Use two workers of one
numerical thread each and a six-hour wall ceiling. Require source-bound
software tests, qualified reboot recovery and a passing short preflight
before launching the eight full tasks. Task-level recovery must reuse sealed
results and charge any interrupted new attempt separately under its finite
allowance.

A technical task passes only with a complete saved fit, forecast, physical
score and earlier-only interval retaining all 26 calibration columns.
Record numerical convergence, original 10 m physical accuracy screen,
known-truth interval coverage and calibration-recovery scores separately.
Any nonpassing task remains in the denominator. Do not promote a technical
pass to physical adequacy. No original or protected aircraft recording is
read. The seven reserved ESA flight groups remain closed. Scientific
decision: **abstain**.
