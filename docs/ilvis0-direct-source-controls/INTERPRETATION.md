# Combined source-bound checks

**All five controls pass.** The direct calibration/rotation remainder and the
reference-point enclosure now work together. Separate exact-rational chains
check narrow and broad gain domains, nonzero calibration, clock-boundary
crossings and deliberately displaced numerical source values and rows.

The study used its 52 bound calls, 18 packet steps, five initializations,
486 rational reference calls and five input-rejection checks. Its saved
evidence and work reservations have been verified. No aircraft recording or
trajectory fit was used.

The next gate installs this bound in the complete native calculation while
retaining the previous valid radii. Predictions and shared coefficient matrices
must stay unchanged; approximation allowances must not widen. All three models
and both processing cases must pass before a full-history usefulness screen.

The previous complete prediction-width result remains four of six generated
groups. These component checks do not establish recording-scale uncertainty,
whole-program floating execution bounds or observational confidence.

[Results](README.md) · [Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
