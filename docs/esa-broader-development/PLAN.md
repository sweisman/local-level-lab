# Broader development intervals: fixed metadata rule

## Selection

Use only the two eligible runs in the verified full-motion inventory for
recording 187. Keep its source hashes, quality criteria and conservative
development group. Do not rerun selection or inspect gyroscope values and
model preferences to choose intervals.

For each run, select its first and last 2,401 receiver records. Each range is
nominally twenty minutes. If the two ranges overlap, retain the first and record
why the last was omitted. Never shift a range to obtain an easier fit.

Within a range, use offsets 1, 3, …, 2,399 as the 1,200 query epochs. The earlier
800 are training observations; the later 400 are prediction observations.
Keep the original first twenty-minute pilot in the inventory as already used,
so it cannot silently become another new test.

All selected ranges belong to the same development group. They can test
consistency over different parts of that recording, but cannot establish
independent replication. Seven ESA confirmation groups remain protected.

## Metadata-only scope

Read the sealed inventory and preparation reports, checking their hashes and
current development membership. Freeze the rule, source/environment binding,
software checks and exact receiver-index ranges before future fitting.
At most sixteen parent runs and thirty-two ranges are supported by this
planning interface; excess metadata is rejected rather than silently truncated.

This step opens no original recording, decodes no measurements and performs
no propagation or fit. It supplies no new timing, speed, heading, latitude or
height statistics for individual windows. Parent-run averages must not be
presented as window averages. The rule requires no numerical thread allocation.

## Later gates

The ranges remain candidates until preparation independently checks their exact
timing, source sequence, full IMU support and unchanged source hashes. Require
actual support duration within half a second of twenty minutes; do not repair
gaps or interpolate measurements. Preserve turns and climbs for explicit motion
reconstruction. Preparation must save window-specific trajectory summaries.

Preparation and model fitting need separately qualified finite definitions
after the current error-assumption assessment. This metadata freeze authorizes
neither step and consumes no fitting allowance. Preserve numerical failures,
physical accuracy failures and all preceding study limits.

[Existing inventory](../esa-development-selection-v2/README.md) ·
[Noisy-data test](../esa-noisy-prediction/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
