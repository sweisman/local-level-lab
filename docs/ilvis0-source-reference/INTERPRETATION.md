# The tighter range also improves the source error allowance

All six generated-source comparisons pass. Every one of the 27 coefficient
columns agrees with an independent rotation calculation. The largest coefficient
difference is about 2.5 × 10⁻¹⁵; the largest value difference is about
1.6 × 10⁻¹⁴ m/s².

The earlier value-only test was not enough to establish a usable propagation
bound. This comparison takes the actual compiled-source reference value and
coefficient row, then calculates a conservative error allowance around that
row. The allowance is 0.00093–0.00097 m/s², compared with the original
0.00305 m/s²: a reduction of about 68–69% in all six groups.

The sources preserve their original training-derived information and calibration
domains. All clock queries lie about 1.3 × 10⁻¹³ seconds from a packet boundary,
so the saved branch convention matters. The native and independent calculations
use the same selected packet. A branch-specific reference row does not establish
a unique two-sided derivative at the boundary; the affine bound remains valid
about the specified row across the supplied interval.

This is an improvement in the calculation, not a new aircraft result. It covers
one body-rotation source term, not every force sample, geographic-frame rotation,
velocity update or position prediction. Carrying the tighter vertical bound
through those operations is the next task. Aircraft prediction fits remain
gated, and the existing 53-stretch findings are unchanged.

[Results and evidence](README.md) · [Next integration task](NEXT_PLAN.md) ·
[Analysis roadmap](../ANALYSIS_ROADMAP.md).
