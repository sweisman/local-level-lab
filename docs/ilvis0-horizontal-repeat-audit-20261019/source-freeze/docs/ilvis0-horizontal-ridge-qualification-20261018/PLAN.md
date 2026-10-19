# Horizontal ridge-probe continuation qualification

## Scope

The completed fixed-point study reproduced all twelve centers exactly. Its
ridge probes passed all twelve unchanged local numerical limits; the original
probes reproduced the four flat-model failures. This qualifies neither a fitting
algorithm nor paired-start repeatability. Preserve the failed parent study.

Test a separately versioned candidate that changes only the local correction
proposal to a column-scaled ridge penalty of 1e-6 on normalized displacement.
The scored physical objective, all nuisance columns, bounds, clock and final
stationarity/cost/physical-motion thresholds remain unchanged. The ridge term
is not included in the model score. It does not identify weak calibration.

## Eight predeclared identities

Continue all four flat-model parent endpoints and the two unsubtracted zero-field
globe endpoints under the same generated observations and physical assumptions.
Add two fresh opposed-start controls, unsubtracted globe-with-field and
unsubtracted flat-disc, using the original full-calibration starts.

Each identity gets at most **200 tangent calls** including fresh checks plus
two diagnostic predictions: **eight starts /1,616 native calls maximum**.
Four numerical threads, thirty minutes, no retries or expansion. No original
recording reads or observed-data fits. Interrupted identities remain charged.

## Acceptance

Require all eight individual controls to pass the unchanged objective/error
checks. Reuse only the six explicitly named passing globe companions from the
parent, yielding exactly twelve primary comparisons and all six paired-start
checks. All must pass, including the previously disagreeing zero-field globe
pair. No outcome-based companion substitutions or relaxed repeat limits.

This study tests an explicitly staged continuation method, not a claim that the
earlier one-stage allowance succeeded. Keep all old fit and qualification labels.
Any subsequent observed study needs its own finite freeze and matched repeats.

Freeze source, input, environment and exact identity hashes before starts;
record each native call before execution, preserve atomic outputs and use
exclusive launch/worker locks. Package-only performs no numerical work. Never
restart a charged or completed batch or borrow another study's unused allowance.
