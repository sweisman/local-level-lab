# The horizontal force check cannot resolve the north–south error

The north–south position error that spans the saved ESA score gap changes
predicted horizontal force by **0.37–0.71 mm/s² RMS** after matching the
time supports. The smallest disagreement with the recorded quartz force
is **2.72 mm/s² RMS**. Moving the quartz clock by 0.1 seconds changes the
comparison by up to **1.87–5.84 mm/s² RMS**, depending on the averaging.
The existing data and timing assumptions cannot distinguish that error
from the original path. [North–south error construction](ESA_MOTION_AXIS_SUPPORT_RESULT.md)

| Zero-field model | Support | Change caused by the error | Quartz disagreement with original path | Quartz disagreement with displaced path |
| --- | ---: | ---: | ---: | ---: |
| Globe | 10 s | 0.71 | 6.68 | 6.44 |
| Disc | 10 s | 0.71 | 6.90 | 6.71 |
| Globe | 24 s | 0.68 | 5.22 | 5.00 |
| Disc | 24 s | 0.67 | 5.80 | 5.56 |

All force values are in mm/s² RMS. The table uses the magnitude of the
averaged horizontal vector with the logged clock. That magnitude is
unchanged by a constant rotation of the two horizontal axes. The
alternative check, averaging instantaneous magnitudes, gives the
smallest disagreement at 10 seconds and much larger discrepancies at
24 seconds. Differences in filter response, platform tilt, time-varying
heading and sensor location can all affect this comparison. Both
zero-field geometries remain in the saved record. No decision about
shape or evidence of an actual north–south error follows from these results.

All ten fixed supports and all clock cases completed. Ten software
tests passed, and the eight summaries reproduced from the saved supports.
No Earth-model fits ran and no reserved flights were opened.
[Frozen plan](ESA_GIRAFE_HORIZONTAL_WITNESS_PLAN.md) · [Sealed result](esa-girafe-horizontal-witness-result.json)

The follow-up tried to preserve direction by learning a fixed horizontal
alignment on earlier data. That alignment left 17–18 mm/s² RMS of
northward disagreement on its separate check intervals.
[Directional transfer](ESA_GIRAFE_DIRECTION_TRANSFER_RESULT.md)
