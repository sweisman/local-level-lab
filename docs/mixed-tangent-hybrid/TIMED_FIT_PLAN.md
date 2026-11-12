# Whole-fit timing gate

## Question

How much CPU time does the selective-precision tangent save during complete
twenty-minute training fits, compared with the existing wide-precision tangent?

## Frozen design

Repeat the six generated cases from the completed long paired-fit study: three
physical candidates by two processing settings at latitude 55°, 1,200 seconds
of 300 Hz IMU increments, 1,199 one-second receiver epochs, and one fixed start
per case. The measurements, split, bounds, optimizer, two tangent
implementations, withheld truth and scoring rules remain identical. The only
new observation is process CPU and elapsed time around each fit. Record both
the complete calculation and the interval from compiled kernel availability
through the saved optimizer fit. Never use timing to select a start or alter a
scientific pass label.

Require the completed six-case long paired-fit study, its source and environment
bindings, and a direct-load test of the new worker adapter. Run four workers
with one numerical thread each. Each pair permits at most 402 native calls;
the six-case ceiling remains 2,412 calls and 464,550,348,000 packet/query
visits. Retain the same finite construction limits, six-hour wall ceiling,
and no outcome-driven retries. Charge before every native calculation.
Keep sealed completed tasks after a technical interruption and preserve charged
unfinished attempts under the frozen recovery rules.

The output reports CPU and elapsed seconds for both variants, their ratios,
evaluations, cost and matched withheld-position difference in every case.
Positive, finite, correctly ordered time markers and both independently
adequate fits are required. The predeclared operational criterion for a
worthwhile substitution is a median wide/selective **fit CPU** ratio above
1.25 and no case below 1.0. This criterion says only whether the optimization
is worthwhile; the already qualified numerical-agreement gate remains separate.
Report the numbers even if the operational criterion fails. Observed-data use
still needs a separate source-bound release; no observed or protected
recording may be read in this study.

## Implementation

- Add a small timing wrapper around the existing paired calculation; do not
  copy the fitting worker or alter frozen historical code.
- Test missing, duplicated and out-of-order markers; test positive times and
  unchanged calculation outputs. Verify a directly loaded frozen adapter.
- Qualify sources/environment/tests before preparation, run within the finite
  allowance, independently replay saved results, then publish and update the
  roadmap. A failed gate remains a recorded failure.
