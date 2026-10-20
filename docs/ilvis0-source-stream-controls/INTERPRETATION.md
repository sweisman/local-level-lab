# Every source midpoint and endpoint now has a checked reference row

All six generated sources pass. The comparison checks every packet midpoint
and endpoint, including all 27 physical columns: 9,600 compiled source steps,
9,600 independent steps and 3,225,600 scalar comparisons in 18.82 seconds.
The largest value difference is about 2.9 × 10⁻¹⁴ m/s²; the largest coefficient
difference is about 4.6 × 10⁻¹⁵.

The native calculation uses a fixed 10,768-byte working state. Packet inputs
remain immutable, and derivative rows are emitted as needed rather than stored
for the entire recording. Independent quaternion/Jacobian calculations agree
with the native arithmetic. Local complex-step matrix-exponential controls also
check nonuniform timing, exact packet boundaries and all coefficient columns.

This removes a reference-map and memory obstacle to using the tighter source
interval throughout a recording. It does not yet connect that interval to
velocity and position calculations or qualify final prediction widths. The next
saved-baseline screen checks what the already-qualified transport layer improves;
the remaining source integration uses these streamed rows.

No aircraft result changed, and no aircraft data or protected ESA data was used.

[Results and evidence](README.md) · [Next task](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
