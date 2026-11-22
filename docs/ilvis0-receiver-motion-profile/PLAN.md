# Receiver motion profile for longer candidate tracks

## Question

What aircraft motion is visible in the 29 receiver/raw candidates selected by
the sealed [232-file inventory](../ilvis0-receiver-raw-inventory/RESULT.md)?
This is a prefit description, not a level-flight or Earth-model decision.

## Fixed method

Freeze the inventory's 29 segment IDs, source hashes, timing contexts and
original files. Reparse only their 29 sources. Require the original candidate
IDs, intervals and source hashes to reproduce exactly. Use each original
ZDA-timed GGA receiver fix; do not interpolate missing measurements. Convert
coordinate differences to local north/east speed using the declared WGS84
receiver-coordinate metric **for motion screening only**. Estimate velocity
and climb from centered 30-second local linear regressions. Estimate course
change from a second centered 30-second regression of the resulting course.
Report coverage, height span, speed, course span and the 95th percentile and
maximum absolute climb and course-change rates for each candidate. Unsupported
edges and gaps stay unsupported. Retain invalid/failing tasks.

The numerical thresholds from the original fused-motion screen (1.5 m/s
vertical speed and 0.05 degree/s course change) are displayed as reference
lines only. This study will **not** assign scientific eligibility or remove
segments based on its results. A later rule must be fixed before any
Earth-model fits and must separately handle roll, accelerations and nuisance
information.

## Execution

One task per candidate source; 29 tasks, one worker and one thread, at most
two hours, no model evaluations. Qualify task-level interruption recovery
before launching. Publish per-candidate and per-source ledgers, including
failures, from sealed results. Preserve the original 53-stretch study and the
reserved ESA groups.
