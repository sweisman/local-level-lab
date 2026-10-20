# Orientation constraints pass but barely narrow the ranges

All 48 sectors passed correctness. Complete ranges narrowed by less than 0.2%
relative to the preceding rotation/gain comparison, with no material height
improvement. The same three of six groups still miss the fixed twofold target.

The calculation took 110.9 seconds and performed no native integration, new
bounds, aircraft fitting or original-file reads. All physical limits, previous
constraints, sectors and 51 coordinates remain. Predictions were saved before
checking the known future outcomes, and every applicable known truth remained
feasible and contained.

The orientation-domain constraint is valid, but its common distance bound treats
all three matrix columns as equally sensitive to every orientation change.
That loses useful structure: rotation about a column's own axis does not move
that column when the perpendicular rotation components vanish. The next
component will bound each column's motion separately.

The prediction method still needs useful recording-scale ranges, adequate
numerical treatment and observational error assessment. The 53-stretch findings
are unchanged; no new aircraft prediction trial follows from this result.

[Every complete range](README.md) · [Next derivation](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
