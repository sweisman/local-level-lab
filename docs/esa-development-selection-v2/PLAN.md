# Full-motion development inventory

## Frozen question

Which complete receiver intervals in development recording 187 meet the
[version-2 rules](../external-imu-data/ESA_SELECTION_V2.md)? This inventory is
independent of gyro values and model-fit outcomes. It preserves the completed
version-1 zero-eligible inventory.

Version 2 uses the qualified full-motion calculation as its intended analysis
method. It retains turns and climbs without declaring them quiet or level.
Duration, speed, distance, quality, timing and full-covariance checks remain
explicit. The working uncertainty floors cannot repair invalid reported covariance.

## Inputs and protected data

Use only `187_air1_ppp_2Hz_final.txt`, the established integrity/support receipts
for `187_rqh01.txt`, the receiver inspection report and the current conservative
group/reservation ledger. Require recording 187 to be explicitly assigned to
development. Unknown or protected membership is a failure before source reading.

The original receiver source remains separately acquired data. Freeze a reference
containing its project-relative path, filename, size and previously established
SHA-256; verify the complete source while decoding. Do not copy the producer's
raw data into publication packs. The source must match the earlier inventory's
hash. No raw IMU is opened; its support comes from the matching full-source
acquisition/inspection receipts. Preserve the original files and metadata.

## Finite allowance

One identity, one worker, one numerical thread, a cooperative 300-second limit,
no retries. At most one original receiver-file pass, 100,000 retained receiver
epochs, 100,001 decoder calls including the EOF lookahead, and one selection
pass. Reserve decoder capacity in blocks of at most 1,024 before parsing;
unused reserved slots remain charged. Charge all custom work through a sealed
journal. Native calls, optimizer starts, raw-IMU reads and protected reads are zero.

Use `lll.studies` for source/environment/input-reference freezes, exclusive locks,
atomic evidence and completion. Capture the actual one-thread numerical
environment before qualification and retain it in the definition. A completed
inventory cannot restart or donate unused allowance.

## Required checks and evidence

Before launch, pass source-bound tests for frozen version-1 compatibility,
full-motion selection boundaries, full covariance/chart validation, development
membership, support-receipt agreement, complete-source hashing, decoder caps,
charge ordering and explicit receiver-only scope. No source is selected because
its model fit looks favorable.

Save all eligible and rejected runs, per-epoch reasons, source/support identities,
policy version, original hashes and charged versus actual work. An empty eligible
list is a valid completed result. Reports read saved selection evidence only;
packaging must not decode again or fit a model.

Publish duration, distance, speed, latitude, heading and sampled-motion summaries
with the inventory. Overlapping or adjacent intervals are not independent flights.
The original receiver coordinates remain conventional geodetic observations.

## Next gate

This inventory authorizes no fitting by itself. The first observed pilot needs
its own preselected interval, raw-source verification, timing support, working
weights, starts, accuracy screens and finite allowance. Protected confirmation
groups remain reserved until their method and identities are frozen.

[Selection rules](../external-imu-data/ESA_SELECTION_V2.md) ·
[Working receiver errors](../ESA_ERROR_POLICY.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
