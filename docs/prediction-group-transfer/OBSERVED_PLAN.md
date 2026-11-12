# Four-group forecast-error transfer check

## Question and fixed groups

Does a forecast-error scale learned from an earlier portion of the three
original NASA development recordings describe later forecasts on four other
preselected conservative flight groups? The four identities and exact receiver
cuts are fixed in [the selection plan](PLAN.md) and [split receipt](split-receipt.json).
This is retrospective development, not an independent statistical validation
or a new Earth-model decision.

## Rule fixed before the four new fits

Use the completed [three-recording rolling-origin study](../prediction-rolling-origin/RESULT.md)
as the reference. For each of its three recordings, take the primary fit chosen
by **earlier training cost** at the first-third cut under the `header_elapsed`
clock and the no-removal processing case. All three first-cut fits passed their
numerical screens. Their north/east/up RMS errors over the next equal-horizon
third are, in metres:

| Recording | North | East | Up |
|---|---:|---:|---:|
| `0e73879f…` | 0.494905 | 4.491069 | 3.342333 |
| `3df34ea3…` | 5.092236 | 19.764265 | 10.778407 |
| `7024120d…` | 2.073988 | 0.321473 | 1.337989 |

The fixed directional reference is the **maximum across these three
recordings**: 5.092236 m north, 19.764265 m east and 10.778407 m up. The
exact stored values, rather than these rounded display values, govern the
comparison. These are an empirical development envelope, **not** a 95%
prediction interval. No multiplier, threshold or preferred four-group result
may be chosen after opening the four scoring periods.
The saved source CSV has SHA-256
`651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117`.
The [shared reference builder](../../analysis/lll/prediction_transfer_reference.py)
checks that hash and the complete twelve-setting grid. Three focused checks
verify the exact maxima, fail on a missing first-cut result, and show that
changing later-cut scores cannot change this reference.

## New calculations and accounting

For each of the four selected groups, use the saved equal-horizon two-cut
layout: fit the first third and forecast the next third; separately fit the
first two thirds and forecast the final third. Reuse the established
specified-field globe training/forecast path, `header_elapsed` clock,
no-removal processing case, unchanged calibration bounds and weights, and
both deterministic starts. Select a primary at each cut by that cut's
earlier training cost among numerically passing fits. Save the forecast before
reading its scoring positions. If neither start passes the numerical stopping
check, mark that cut unqualified; do not pick a start by later error or replace
a failed result. Separately report the original physical prediction screens:
horizontal RMS ≤ 10 m, height RMS ≤ 30 m, maximum horizontal error ≤ 50 m
and maximum absolute height error ≤ 150 m. These screens are outcomes, never
used to choose a start or an error envelope.

The finite grid is **4 groups × 2 cuts × 2 starts = 16 charged starts**.
Allow at most **200 training native evaluations and one forecast call per
start**, for **3,216 native calls maximum**. Freeze packet-visit limits from
the exact prepared packet counts. The [study adapter](../../analysis/lll/ilvis0_group_transfer_study.py)
fixes one worker with one numerical thread and a cooperative **12-hour** wall
limit. Source and environment hashes, prepared input hashes and the task-level
recovery evidence must be sealed before launch. The active ESA paired study
reserves three of four numerical threads; this transfer study must not exceed
the remaining one while it runs. The adapter reuses the earlier rolling-origin
evaluator only if all of its frozen source files still match the sealed prior
study. Qualify that evaluator on generated two-cut controls and prove reboot
recovery. Reuse sealed completed failures and never reset charges.

## Reporting gate

Report all 16 starts, every numerical or physical failure, and each
training-selected first-cut and second-cut directional RMS and height error.
Compare the four **second-cut** errors with the fixed three-recording
reference, and report the fraction of groups whose three axes stay within it.
Also report each group's first-to-second-cut ratio; do not treat repeated
starts as independent flights. A failed or unavailable second-cut fit is an
abstention and stays in the denominator. Record duration, horizon, IMU type,
latitude and provenance group beside each result.

The diagnostic asks whether a simple empirical error scale transfers. Four
new groups cannot calibrate rare-error coverage. Passing this check would
still leave a physically justified aircraft error law, gyro-specific
contribution, absolute adequacy and protected ESA confirmation open. Failing
it would rule out this simple scale for further use; it would not alter the
53 saved shape comparisons.
