# Validate the old recording format against the current input API

Use the three frozen broad four-minute generated inputs from the earlier
recording-scale study. Preserve all 48,000 periods, angle/velocity increments,
calibration limits, initial coordinates, velocity and literal mounting matrix.
Declare fixed-zero and profiled removal as separate processing variants. Do
not use the narrower sensitivity inputs as measured calibration.

The format adapter passes 19 deterministic checks. These new controls compare
the unchanged legacy tangent-call wrapper with the current array-call API,
using the same compiled qualified kernel through its two calling conventions.
Check predictions, all 27 Jacobian columns and warning flags bit-for-bit at
five seconds, at zero and one fixed nonzero parameter vector. This validates
data/API equivalence, not independent physical truth or uncertainty bounds.

## Finite allowance

- Six identities: three candidates under both processing variants.
- Four native API queries per identity, 24 total; at most 1,152,000 conservatively
  charged packet visits. Zero interval bounds or propagation-bound steps.
- One worker and one numerical thread; 120 seconds overall, no retries/signals.
- No LP proposals, optimizer starts, original-aircraft reads or protected ESA
  outcomes. Compilation uses frozen source and the recorded installed compiler.

Freeze original and converted input hashes, source/ABI definitions and numerical
environment before execution. Reject malformed clocks and nonfinite or missing
values. Do not normalize the mounting matrix, round timestamps or change units.
Keep the original fixed-clock limitation explicit; this does not qualify an
uncertain integration clock or transfer a short-history training certificate.

All six cases must pass before a separate costed recording-duration screen.
Successful API comparison alone establishes neither useful four-minute bounds
nor an adequate observation-error model. Preserve every earlier failure.

[Short-example gate](../ilvis0-three-source-complete/INTERPRETATION.md) ·
[Earlier four-minute outcome](../ilvis0-recording-scale-bounds/INTERPRETATION.md).
