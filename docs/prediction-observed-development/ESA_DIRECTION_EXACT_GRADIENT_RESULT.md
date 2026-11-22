# The saved calibration points fail the exact stopping check

The exact packet-based gradient exceeded the declared limit at **all
108 saved proposals**. The previous approximation accepted 102 of
those points. The later direction errors at those points are still
valid replays. The new check shows that none was an eligible stopped fit
for the exact training calculation, so no matched comparison is fully
qualified under that check.

| Exact check | Result |
| --- | ---: |
| Saved proposals audited | 108 |
| Passing prepared approximate gradient and exact replay check | 102 |
| Passing exact gradient | 0 |
| Matched settings with both shapes passing | 0 of 18 |
| Exact projected gradient at the 36 originally selected points | 2.74 × 10⁻¹⁰ to 3.09 × 10⁻⁸ |
| Declared exact gradient limit | 10⁻¹⁰ |

In the GLONASS setting where the disc had the smaller later angle error,
the exact gradient was **1.25 × 10⁻⁸** for the disc and **2.95 × 10⁻⁸**
for the globe. The size of the earlier replay mismatch alone did not
detect this change in stopping behavior. The saved comparison remains a
sensitivity result at explicit calibration points. Its ranking is not a
comparison of exactly stopped fits.

The earlier losses reproduced the original exact replay values. The
calibration derivative after accounting for the starting rotation had
local rank 11 in all 108 checks. The common accelerometer gain scale
remains unobservable from directions alone. Nine focused tests passed,
including a comparison with finite differences of independent ordered,
noncommuting rotations. No new calibration search or later scoring ran.

The first release rejected the array-library integer used for the packet
count before charging any work. Its failure is retained. The corrected
freeze audited all 108 points using 59,866 earlier intervals per point.
The original position forecast's later values and all reserved flight
groups stayed outside the calculation.

## Reproduce the saved check

With the closed `data/esa-direction-exact-gradient-v2` study restored,
verify the audit and the charged work without running a new search.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_exact_gradient report
```

[Frozen design](ESA_DIRECTION_EXACT_GRADIENT_PLAN.md) ·
[All projected gradients, earlier losses and ranks](esa-direction-exact-gradient-result.json)
