# Tightening calibration ranges lowers the bound to 53.10 units

The archived training constraints tightened **20 coordinate ranges** across
all eleven surviving calibration boxes. All eleven score bounds improved.
The combined upper bound fell from **53.20 to 53.10 units**, still above the
**25.41-unit** forecast gap. The zero-field comparison remains unresolved
over the full allowed calibration range.

| Candidate | Surviving boxes checked | Coordinate ranges tightened | Previous bound | New bound |
| --- | ---: | ---: | ---: | ---: |
| Zero-field globe | 5 | 11 | 20.649 | 20.649 |
| Zero-field disc | 6 | 9 | 32.546 | 32.456 |

Each individual globe bound fell slightly. The previously verified bound
over the complete globe cover was already lower, so the overall globe
bound stayed at 20.649. Four disc children retain individual bounds above
25.41 units. Tightening the globe alone cannot close the gap. The largest
retained disc bound is in child 1 of range 3/2 at 32.456 units. The other
high disc child in range 2/2 stays at 31.784 units.

The contracted box keeps one interval per coordinate. The original
inequalities also couple coordinates within each box. The saved
projection rows make it possible to test a direct bound on the signed
score that keeps those couplings, using the same earlier loss limit.

The [frozen calculation](ESA_LINKED_COORDINATE_PLAN.md) used all 60 columns
of the saved inequalities to contract the physical box. It derived bounds
for both signs of every physical coordinate and checked the proposed dual
weights with exact arithmetic. It then used one shared physical calibration
map to recompute the earlier score certificates. All saved feasible points
still lie in their contracted ranges.

All eleven tasks completed within 283 seconds and used the 682 charged
operations. The check made zero trajectory fits or reserved-flight reads.
The smaller bound applies to the saved static calibration map under the
original training allowance. The full integration remainder and aircraft
error coverage remain open. [Per-child bounds](esa-linked-coordinate-result.json)

[Source and execution receipts](esa-linked-coordinate-evidence/README.md) ·
[Verified reproduction bundle](esa-linked-coordinate-evidence/bundle.zip)
