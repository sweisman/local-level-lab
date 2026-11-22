# Alignment-status screening ablation

## Question

Among the 29 sealed receiver/raw candidate sources, how many satisfy the
original ten-minute, 50-km speed, climb, roll and course-change checks if the
Applanix fused-navigation **alignment status alone** is not required?

## Fixed comparison

Use the same 29 original files, source hashes and timing contexts as the
[receiver/raw inventory](../ilvis0-receiver-raw-inventory/RESULT.md). Keep
the 180 km/h receiver-speed floor, ten-minute duration, 50-km sampled path,
two-second receiver gap, original Group-1 climb/roll/course thresholds,
turn buffers and Group-4 completeness rule. Change only the alignment-status
veto. Retain its per-sample flag count as a diagnostic. Do not inspect gyro
model residuals or fit an Earth model.

Group 1 is fused navigation. Its motion values are screening context, not
independent curvature or rotation evidence. If alignment is false, these
values may themselves be less reliable; candidate recovery here therefore
does **not** establish eligibility. Compare recovered tracks later with the
independent receiver-motion profile, raw continuity, mount status and full
nuisance information under a separate rule.

One source is one sealed task. Freeze all 29 identities, policy, code,
environment, charges, one-worker/one-thread allocation and a two-hour
cooperative limit. Qualify task-level reboot recovery first. Preserve empty
and failed results; publish a source and candidate ledger. The original
53-stretch study and seven reserved ESA groups remain unchanged.
