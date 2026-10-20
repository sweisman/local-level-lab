# Tighter coordinate boxes give only a small improvement

All **48 future-bound recomputations pass**, completing all six cases with the
same orientation coverage and 42 columns. Complete widths now range from
**0.616 to 2.889 m**, compared with 0.620–2.973 m previously. The improvement is
only **about 0.4–2.9%**.

This tests the practical benefit of the certified coordinate projection:
smaller velocity, position and common-acceleration boxes are mathematically
valid, but they do not substantially reduce the current prediction ranges.
Repeating larger coordinate searches is therefore not the next priority.

The study reused saved native predictions, derivatives and training data. It
made 48 future-bound calculations, with no new native integration calls,
original aircraft reads or observed fits. All known-control checks pass.
These remain generated engineering ranges, not measured aircraft errors or
calibrated prediction intervals. The 53-stretch empirical result is unchanged.

The next diagnostic should expose how the propagation allowance accumulates,
especially its position component, while reproducing the current arithmetic
and bounds. Any tighter mathematical construction needs its own proof and
qualification. Recording-scale usefulness and observation-error adequacy remain
open before new aircraft prediction comparisons.

[All six comparisons](README.md) · [Frozen scope](PLAN.md) ·
[Coordinate projection](../ilvis0-joint-constraint-projection-v2/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
