# Longer-flight candidate inventory

## Question

Do the 232 retained airborne recordings contain enough additional, distinct
level-flight groups to investigate prediction coverage beyond the original
53 selected stretches? This inventory does not fit an Earth model.

## Fixed selection

Use `ilvis0-distance-duration-inventory-v1`. A candidate is one maximal
continuous interval with at least 600 seconds and 50 km of sampled primary
receiver path. Every supported receiver ground-speed sample must be at least
180 km/h. Retain the original alignment, roll, vertical-speed, course-rate,
gap, maneuver-buffer, raw-completeness and timing rules. Group 1 fused
navigation supplies motion screening only. The checksummed primary receiver
supplies speed and position. No gyro increments or model residuals determine
which interval passes.

The 50 km threshold slightly exceeds the original four-minute, 700-km/h
minimum path length of 46.7 km. The lower speed floor permits a longer survey
leg to qualify while excluding ground movement. These are inventory rules,
not a calibrated information or detection threshold.

## Inputs and execution

Use exactly the 232 source paths and SHA-256 values in the retained corpus
inventory, with their existing timing contexts. Each file is one separately
sealed task. Before scanning, freeze this plan, the policy, source code,
numerical environment, input hashes, one-worker/one-thread allocation and a
finite task/wall allowance. Verify task-level recovery on interrupted work.
The scan reads originals but does not duplicate or delete them. Unsupported,
corrupt or incomplete files remain recorded as failures, with their hashes.

After all tasks close, publish a file ledger and candidate interval table.
Merge byte-identical aliases. Group overlapping instruments and adjacent
intervals conservatively by actual UTC and recorded flight provenance.
Report both candidate count and conservative group count; do not call either
an independent calibration sample until independence is supported. The
original 53-stretch selection and all saved fits remain unchanged.

## Next gate

If enough distinct candidate groups exist, assess geometry and model
information using a separately frozen study before any observed model fits or
coverage claim. The seven reserved ESA confirmation groups stay closed.
