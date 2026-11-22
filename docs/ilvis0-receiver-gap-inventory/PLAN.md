# Receiver gap inventory for the 53 selected stretches

## Question and fixed cohort

For each of the 53 previously selected high-speed level stretches, how much
primary-receiver position coverage remains in uninterrupted blocks? Reuse the
published selected-stretch table and the completed primary-receiver enhanced
position inventory. Its one strict-decoder failure stays in the 53-task cohort
as a failure; do not replace or repair it.

This is a GPS-only completeness inventory. It reads no IMU increments or fused
navigation and makes no Earth-model fit or decision. Existing stretch selection
and model preferences remain unchanged.

## Time and block policy

Convert each selected UTC boundary to GPS time using the recording's saved leap
second count. Retain saved receiver positions inside the original complete
stretch, with no interpolation. Split at any adjacent receiver-time gap above
**1.5 seconds**; retain every source row index and every rejected short block.
A block needs at least **five** receiver positions to pass this completeness
screen. These settings match the software support policy's one-second receiver
expectation; they are not an Earth-model acceptance threshold.

Report all block durations, row counts, gap lengths, original table hashes and
failure reasons. Do not count adjacent blocks or overlapping recorders as
independent flights.

## Finite execution and evidence

Stage the 52 accepted published position tables by verified SHA-256, along with
the published 53-stretch selection and prior decoder outcomes. Freeze source,
environment, staged inputs, task IDs and this plan before running. Use one
worker and one numerical thread, at most 53 task starts, zero native model
calls, zero bound calls and a 20-minute cooperative wall ceiling. A task
failure is retained; no alternate decoding or retries change its outcome.

Publish a verified per-stretch table and a concise summary only after all
tasks seal. This inventory can prepare the later gyro-free comparison but
cannot calibrate receiver error, support-selection uncertainty or a scientific
detection.
