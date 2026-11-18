# Whole-period generated prediction: runtime-qualified cohort

The previous 96-recording cohort closed with 92 paired forecasts and four
sealed stops at its eight-hour time limit. Every later coordinate in the 92
scored recordings fell within both reported intervals. The four stops count
as failures, so that cohort did not pass its prespecified 5% gate. This is a
**new** cohort; none of those 96 tasks will be rerun or relabeled.

## Frozen question

On 96 independent generated recordings drawn from the same equal-weight
24-condition mixture, do training-only, two-law whole-period intervals contain
every later coordinate of both the physical position and a separate receiver
report? Both model fits must pass numerical stopping and the physical prediction
screen. Every technical error counts as a failed recording. At most one failed
recording is permitted by the exact one-sided 95% upper failure-rate gate of 5%.
The result applies only to this generated mixture. It cannot establish coverage
on observed aircraft or make an Earth-model decision.

## Unchanged scientific method

Keep the previous two-minute trajectory, 300 Hz IMU, 119 receiver epochs,
200 fit evaluations per law, physical parameter bounds, two forecast targets,
two-law affine interval union, and 95% joint conditional allocation. The
synthetic trajectory, sensor-error generator, training-only fitting, prediction,
interval construction and scoring stay unchanged. Use 96 new distinct recording
noise seeds and a new mixture seed disjoint from both prior cohorts. The study
identity is `prediction-simultaneous-law-family-v3-runtime-20261112`; the
mixture draw seed is `31415927`, and recording noise seeds are
`31415927000` through `31415927095`.

## Finite runtime allowance

The previous cohort used eight hours and then required about one additional
hour for 12 unstarted tasks. This new study allows **12 hours** for all 96
tasks, using four workers of one numerical thread each and no more than four
total threads. The twelve-hour limit is a fixed reserve for measured runtime,
not a permission to alter a scientific result. Native and construction calls
remain limited per task as before. Require at least 35 GiB free space at launch.
Cooperative stopping, exclusive leases, durable charges and sealed results
remain mandatory. The idempotent recovery command verifies source, environment,
receipts and leases; it may finish only genuinely unfinished work under a
separately charged finite allowance. Sealed failures cannot be retried.
The [recovery procedure](RECOVERY.md) gives the idempotent commands.

## Release order

1. Pass the full Python suite and source-bound software and recovery checks.
2. Freeze this plan, exact seeds/tasks, sources, environment, input hashes,
   worker count, per-task limits and study-wide wall limit.
3. Run a separate short preflight through the actual frozen worker loader.
   Check that both forecast targets are saved before later truth is revealed.
4. Launch the 96-recording study only after preflight and reboot-recovery
   qualification pass. Preserve every charge and result.
5. Publish a saved-data audit: replay both target scores, verify hashes and
   source binding, count failures by recording and condition, and calculate
   the exact upper bound. Publication performs no fit.

If the technical or coverage gate fails, keep its original outcome and diagnose
it separately. Protected observed-flight groups remain closed.
