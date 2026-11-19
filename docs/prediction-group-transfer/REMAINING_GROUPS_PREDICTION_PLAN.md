# Forecast adequacy across the remaining selected NASA groups

Use the [20-group outcome-blind inventory](EXPANSION_INVENTORY.md) unchanged:
one longest eligible stretch per conservative group not used by the original
three-recording pilot or four-group transfer check. This is a retrospective
development extension, not untouched confirmation. All 20 representatives
are IMU21; 18 are southern. Keep those limitations in every report.

Repeat the **same narrow prediction rule** as the first four-group transfer:
the specified-field globe, no upstream removal, `header_elapsed` clock,
existing calibration bounds and weights, two earlier training cuts and two
predeclared starts per cut. Choose among numerically passing starts by
earlier training cost only. Forecast the next equal-duration receiver block
before opening its positions for scoring. Preserve the earlier fixed
three-recording directional RMS reference (5.092236 m north, 19.764265 m
east, 10.778407 m up at stored precision) and separate physical screens:
horizontal RMS ≤10 m, height RMS ≤30 m, maximum horizontal ≤50 m and
maximum absolute height ≤150 m. Never change these values after fitting.

The grid is **20 groups × 2 cuts × 2 starts = 80 charged starts**. Maximum
201 native calls per task, 16,080 total; packet visits use exact prepared
packet counts. Four one-thread workers, cooperative wall limit six hours.
The earlier 16-start run took 5,216 seconds on one thread, suggesting about
two hours with four workers if work scales similarly. Prove source-bound
qualification and task-level reboot recovery before launch. Charge before
execution and reuse sealed successes and failures without restarting them.
The 20 groups remain in the denominator even if numerical fits fail.

The first qualification request passed 12 software tests, but preparation
stopped before reading originals because it required every historical source
file to remain byte-identical. Twelve files changed since the sealed
three-recording study: six ESA modules, two generated-noise modules, study
runtime/testing plumbing, the shard loader and the NASA segment-inventory
module. None is the rolling forecast evaluator or its numerical equations.
The segment extractor's syntax tree is identical to the sealed version; the
changed segment functions concern new inventories. The corrected gate
requires this exact audited change set, verifies the unchanged extractor,
and pins the current full source/environment in a new qualification request.
Any further source change requires fresh qualification. No observed start
was charged in the failed preparation.

Report each group's two-cut numerical status, forecast error and physical
screen. This probes descriptive prediction transfer within the same archive.
It does **not** compare globe against flat on these withheld paths, calibrate
an aircraft error distribution, count 20 independent flights, or alter the
original 53-stretch numerical result. Seven reserved ESA groups stay closed.
