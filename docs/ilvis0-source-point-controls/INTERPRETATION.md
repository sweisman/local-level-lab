# Reference-point derivative checks

**All seven controls pass.** They check the force-source values and all 27
calibration derivative columns against a separate exact-rational rotation
calculation. The checks include noncommuting rotations, nonzero calibration,
both packet phases and the clock origin and packet-end conventions.

The study used its 20 source calls, 20 packet steps, six initializations,
115 rational reference calls and seven input-rejection checks. It read no
aircraft recordings and performed no trajectory fits. Its saved evidence and
work reservations have been verified.

This supplies the point-derivative component needed by the proposed tighter
prediction bound. The next step is to combine it with the independently checked
calibration and rotation-product remainders, and account explicitly for the
numerical source values and rows used by the integrator. Then the complete
candidate must pass native controls and a full-history usefulness screen.

No aircraft prediction range or scientific conclusion changes from these
component checks. The last complete prediction-width comparison still passes
four of six generated groups.

[Results](README.md) · [Frozen scope](PLAN.md) ·
[Construction](../ilvis0-eastward-growth/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
