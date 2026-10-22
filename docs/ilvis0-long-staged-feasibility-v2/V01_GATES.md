# What remains before aircraft prediction fits

The completed test asked whether training constraints could narrow a prediction
at 438 seconds after integrating the complete history. All six calculations
finished, but none met the fixed width target. V01 remains unqualified.
The next step is to identify which saved error allowances make the ranges so wide.

| Requirement | Current position | Completion evidence needed |
|---|---|---|
| Useful long-history ranges | All six generated cases retained the known answers but gave unusably wide ranges. The completed study cannot be restarted. | A separately qualified method must pass the fixed width, truth-retention and exact support checks. Containment alone is insufficient. |
| The whole prediction period | This study checks one late endpoint. | Supported ranges at every declared prediction epoch, or a verified enclosure covering the intervening times. One endpoint cannot qualify all 147 withheld epochs of the earlier plan. |
| Receiver and IMU errors together | The joint operator and a small staged connection pass software checks; simultaneous allowances retain one full-period probability budget. | Support for the declared error family over aircraft records, including its approximation and noise-scale assumptions. No candidate-specific inflation or future-data tuning. |
| Numerical and timing treatment | Packet, geographic, rotation and midpoint-step derivatives pass focused controls, alongside piecewise error arithmetic. | Complete packet-to-position qualification, useful full-history derivative bounds, verified clock/rotation partitions and jumps, and native execution allowances. A matching packet-boundary counter does not prove smooth derivatives there. |

The generated ±1-metre training allowance is not an empirical aircraft error
model. Neither a successful endpoint nor a small numerical residual completes
V01 by itself. Failed cases and unsupported regions remain reported.

The separate [zero-reference ray audit](../ilvis0-ray-probes/INTERPRETATION.md)
finds 21.75 m north spread among calibrations satisfying all its earlier
±1 m coordinate constraints. That fixture cannot meet a 20 m north-width target
by improving enclosure arithmetic alone. It is not the result of this study’s
perturbed observations, and it does not justify changing this frozen run.

The [original-observation audit](../ilvis0-truth-probes/INTERPRETATION.md)
checks twelve fixed alternatives against the actual five noisy training epochs.
Six pass; their sampled north spreads are 13.33 m and 5.90 m. This does not
demonstrate a width-target violation for those observations, or provide the
required outer enclosure.

Once these requirements qualify, V02 can test genuinely unused positions,
including height, under a separately frozen retrospective development study.
No such new aircraft fits are part of the current run.

[Completed study](README.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md)
