# Smaller prediction ranges, with an unmet target

All **48 generated cases pass the numerical checks**. Keeping one calibration
transform shared across changing accelerometer samples reduces complete
prediction widths by **40–66%** against the stronger preserved baseline.
The ranges now span about **0.22–1.72 metres at 7.2 seconds**.

The study required at least a twofold reduction on every axis in every case.
**Three of six model/processing groups meet that target; three do not.**
Both specified-field globe groups miss it, as does the profiled-removal
zero-field globe group. This is useful progress, but not a passed long-record
qualification. The target and the original failures remain unchanged.

All eight orientation sectors, 27 physical coordinates and 24 shared-error
coordinates remain. The same generated inputs, physical bounds, training times
and future epoch were used. The run completed in about 50 minutes, spending
144 native calls and 384 bounds. No aircraft measurements were fitted.

The independent [saved-evidence audit](../ilvis0-transform-prediction-audit-v2/README.md)
passes all 48 cases and 288 exact support checks. It reconciles source bindings,
coefficient blocks and outward prediction endpoints. Unshared allowances make
up 28–37% of individual widths; at least 86% of that allowance follows position
propagation. All 24 separate auxiliary coordinate ranges remain unchanged,
although joint constraints still retain correlations.

The [next component](NEXT_PLAN.md) tests necessary relationships between errors
that the current calculation bounds separately. It must preserve physically
possible calibrations before any saved-case narrowing comparison. Broader
recordings, a new aircraft prediction run and protected ESA evaluation do not
follow from this result.

These ranges describe a conservative calculation on generated inputs. They are
neither measured aircraft errors nor calibrated scientific intervals. The
published 53-stretch comparison is unchanged.

[Full results](README.md) · [Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
