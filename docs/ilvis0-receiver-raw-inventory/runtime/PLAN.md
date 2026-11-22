# Receiver-supported flight candidate inventory

## Question

How many longer airborne trajectories in the retained 232-file archive have
complete primary-receiver and raw IMU support if selection does not depend
on the instrument's fused navigation alignment flag? The preceding
[strict-level inventory](../ilvis0-distance-inventory/RESULT.md) found no new
recorded-date group. Its overlapping [rejection tallies](../ilvis0-distance-inventory/REJECTION_AUDIT.md)
motivate this separately versioned, exploratory check. No Earth-model
outcome determined this policy.

## Fixed technical rule

Use checked Group-10001 GGA and VTG sentences, their unique time association,
and the same strict Group-4 timing/status/configuration checks as the earlier
inventory. A candidate must have at least 600 continuous seconds, 50 km of
sampled receiver path and every receiver speed sample at least 180 km/h.
Receiver gaps above 2 seconds split candidates. Remove 10 seconds from the
ends of receiver-supported spans and keep a 0.2-second raw IMU guard. Do not
use Group-1 alignment, roll, vertical speed or course-rate flags to select.
Group 1 may still support packet timing validation, but it supplies no
Earth-model evidence here.

This broad rule does **not** establish level flight or physical adequacy.
Turns, climbs and unmodeled motion may remain. It records possible source
groups for a later, independently fixed geometry/motion qualification. No
candidate enters the original 53-stretch study or a scientific decision.

## Execution and interpretation

Freeze the exact 232 source paths, hashes, timing contexts, source code,
policy, environment, task starts, four-hour wall limit and one-worker/
one-thread allocation. One sealed task scans one original file; no copy of
the original or model fit is needed. Test task-level interruption recovery
before launch. Preserve invalid and empty results. Publish a file ledger,
candidate table and conservative recorded-date groups after closure.
Same-day and overlapping recorders do not count as independent flights.

Next, assess receiver geometry, motion and nuisance-model information on
these candidates under a separate frozen rule. Do not open the seven reserved
ESA groups or claim coverage from this inventory.
