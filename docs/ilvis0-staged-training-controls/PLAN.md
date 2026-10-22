# Keep earlier constraints when refining a long prediction

A long-record calculation can use early training observations to tighten a
bound, then use that bound at later training times. Every refinement must retain
the earlier constraints that justified it. Discarding them could make an
apparently narrow prediction invalid outside the forgotten region.

First qualify a pure constraint-merging component. Require the same source,
reference, units, center, arithmetic allowance and parameter dimensions. Preserve
every earlier inequality and add the new inequalities. Intersect the declared
boxes without rounding inward; never remove a parameter because it is weakly
identified. Support the existing 51- and 78-coordinate schemas, retaining all
27 physical directions in either case.

Cheap deterministic tests check feasible witnesses with exact rational arithmetic,
nonzero centers, narrower and broader incoming boxes, owned outputs, repeated
refinements, source/coordinate changes, missing columns and invalid values.
No optimizer, integration, aircraft data or protected outcome is involved.

Then qualify the complete staged native path on small generated known-answer
cases before a separately frozen complete-horizon comparison. Keep the current
physical bounds, explicit clock support and stated observation-error allowances.
Training data alone can condition the later bounds; future observations cannot.
Any bound justified only on the retained training region remains restricted to
that region.

This is necessary-constraint arithmetic under supplied assumptions. It does not
establish an observation-error law, floating-point enclosure of the full native
program, or useful recording-length ranges by itself.

## Finite native qualification

Six generated cases cover all three candidates and both processing assumptions.
Each uses the unchanged small native-control configuration, 32 packets at
200 Hz, training epochs 0.015/0.03 seconds followed by 0.06/0.09 seconds, then
a prediction at 0.13 seconds. The existing control clock limit is ±0.001 second;
all 27 physical directions remain. These small bounds are not transferred to
the eight-minute inputs or aircraft data.

Per case: ten native queries, five bounds, one physical acceleration proof,
two training-conditioned proofs, eighteen LP proposals and sixty-six exact
support evaluations. Charge 9 × 32 logical steps per bound, plus separately
reserved source/reference/derivative/point work. The total allowance is
**60 native queries / 1,920 packet visits / 30 bounds / 8,640 logical steps**.
Six identities, one worker and one numerical thread; expected one to two
minutes with a fixed five-minute cooperative ceiling. No retries or signals.

Require exact retention of both stages' necessary constraints, matching source
bindings, independent future-endpoint verification and a known feasible witness.
Generate the future witness only after saving the prediction. Store all native
warning bits, compilation metadata, reservations and failures. Passing qualifies
the staged software path only; complete-record usefulness remains a separate gate.

[Complete-horizon requirements](../ilvis0-three-source-complete/NEXT_PLAN.md) ·
[Measurement allowances](../ilvis0-recording-training-interface/INTERPRETATION.md).
