# Earlier drift helps with later height errors and hurts horizontal accuracy

On the twenty NASA recording groups, a correction learned from the
earlier forecast reduced later height error in **15 of 20** groups.
It reduced horizontal error in only **3 of 20**. The same contrast
appeared among the five groups with passing numerical fits at both cuts.

| Group set | Median height RMS before / after | Height improved | Median horizontal RMS before / after | Horizontal improved |
| --- | ---: | ---: | ---: | ---: |
| All 20 groups | 4.70 / 2.08 m | 15/20 | 2.01 / 3.16 m | 3/20 |
| Five groups with two passing cuts | 5.20 / 3.60 m | 4/5 | 2.15 / 3.26 m | 1/5 |

All 20 raw forecasts met the fixed accuracy screen. The correction
raised one later horizontal RMS to 11.88 m, past the 10 m limit. That
forecast already lacked a passing numerical stop. All five groups with
two passing cuts continued to meet the screen after the correction.

The correction uses one offset and one slope for each axis. It was
learned from the earlier forecast errors and saved before the later
errors were opened. The comparison leaves the original forecasts and
stopping labels unchanged. The earlier scoring period can be part of
the later forecast's calibration period. This is a test across time
blocks of the same recording, and it supplies no independent-flight
coverage or estimate of instrument drift.

The [separate height-only check](HEIGHT_TRANSFER_RESULT.md) then reduced
height error in seven additional groups. The original results give little
support for transferring the full three-axis correction. All 20 tasks
completed without a new navigation fit.

[Frozen plan](ERROR_TRANSFER_PLAN.md) ·
[Per-group scores and original stopping labels](error-transfer.json) ·
[Verified evidence bundle](error-transfer-evidence/replay.zip)
