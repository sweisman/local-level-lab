# Linear repair did not produce valid alternatives

**None of the four new calibrations passes the original training constraints.**
The numerical diagnostic completed in 59.49 seconds, using four native batches.
Each linear system had rank 16 and a small linear mismatch, but the nonlinear
training errors reached approximately 4–19 m against the unchanged 1 m limit.

The independent audit recomputes exact differences from the saved positions,
checks all 27 physical coordinates and the linear equalities, and verifies the
charged work. It uses no new native predictions or linear solves. All four
nonlinear failures are retained.

The linear corrections were substantial: their largest normalized coordinates
ranged from 0.091 to 0.248. Agreement in the tangent calculation did not survive
that movement through the nonlinear calibration model. This method is not a
qualified way to construct training-compatible alternatives.

The zero sampled spread in the generated results table means that no new point
qualified, leaving only the known truth in that table. It is **not zero
uncertainty**. The earlier accepted original-observation probes and their
13.33 m / 5.90 m sampled north spreads remain valid. No target violation has
been established for those original observations, and no useful outer bound
has been proved.

No aircraft results, training observations, physical bounds or frozen study
allowances changed. Full-history uncertainty and the aircraft error model remain
open requirements.

[Saved results](README.md) · [Frozen limits](PLAN.md) ·
[Original probes](../ilvis0-truth-probes/INTERPRETATION.md)
