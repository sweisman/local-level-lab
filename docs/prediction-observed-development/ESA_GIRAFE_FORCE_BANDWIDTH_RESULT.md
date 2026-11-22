# Matching the averaging removes most of the airborne force gap

The median GIRAFE-minus-iMAR difference fell in magnitude from
**27.24 to 0.47 mm/s²** when we averaged iMAR's vectors in the same
0.1-second cells as GIRAFE before taking magnitudes. That accounts
for about **98%** of the median signed discrepancy. Raw iMAR
samples capture variation inside those cells. Averaging their
magnitudes first makes all of that variation contribute positively.

| Averaging method | Median later difference | Median later RMS after subtracting an earlier offset |
| --- | ---: | ---: |
| Magnitude of each original sample | −27.24 mm/s² | 2.26 mm/s² |
| Average iMAR vectors in GIRAFE's 10 Hz cells first | −0.47 mm/s² | 0.17 mm/s² |
| Average the vectors of each sensor over the entire support first | −0.44 mm/s² | 0.17 mm/s² |

The median uses both averaging widths on eight windows of one
flight. Each setting measures the offset on its first eight
supports and assesses the following eight. In seven windows the
mean paired gap after matching time cells was 0.29–0.56 mm/s²
in magnitude. The first window retained 2.55–3.18 mm/s² and
larger later residuals. It was the only window with a recorded
change in the atom instrument's interrogation time. The comparison
leaves the cause of that window's disagreement open.
[Interrogation-time inventory](../external-imu-data/esa-girafe-187-acceleration-inventory.json)

The averaging order explains most of the measured raw-magnitude gap.
Matching time cells leaves the instruments' internal filters and
platform behavior unmeasured. The result supports using matched
averaging before estimating an airborne error allowance. It gives
no calibration of absolute accuracy or independent-flight coverage.
[Ground reference](ESA_GIRAFE_GROUND_TIES_RESULT.md) ·
[Original force comparison](ESA_GIRAFE_FORCE_OVERLAP_RESULT.md)

All eight tasks reproduced the original averages and checked that
rebinning preserved each weighted vector integral. The sealed
ledger charges 957,720 iMAR intervals and zero calibration fits.
[Frozen design](ESA_GIRAFE_FORCE_BANDWIDTH_PLAN.md) ·
[Per-support magnitudes and charges](esa-girafe-force-bandwidth-result.json)

To verify the saved report, restore `data/esa-girafe-force-bandwidth-v1`
and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_force_bandwidth report
```
