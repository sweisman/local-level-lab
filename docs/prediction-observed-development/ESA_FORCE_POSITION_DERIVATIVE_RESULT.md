# Position-derived force agrees across receivers and fits GIRAFE less closely

Computing acceleration from positions reduced the differences between
the three receiver products in **all 256 matched comparisons**.
Against the separate GIRAFE measurement, the median later error
increased from **1.30 to 3.62 mm/s²**. Only 32 of 384 matched individual
force predictions improved. The two derivative methods used the same
time supports, Earth models, gravity assumptions and earlier-offset
rule.

| Later comparison after subtracting an earlier offset | Reported velocity method | Position derivative method |
| --- | ---: | ---: |
| Median change when swapping receiver products | 0.743 mm/s² | 0.116 mm/s² |
| Median difference from GIRAFE | 1.295 mm/s² | 3.621 mm/s² |
| Median difference from raw iMAR | 2.131 mm/s² | 4.836 mm/s² |
| Median globe–disc difference, zero field in both | 0.0282 mm/s² | 0.0282 mm/s² |
| Median globe–disc difference, specified field in both | 0.0260 mm/s² | 0.0260 mm/s² |

The median change from using position derivatives was 4.08 mm/s²
for individual force predictions. The receivers share an antenna,
and closer agreement between their products was a poor guide to
agreement with an independent instrument in this test. The
force-only shape result remains unresolved. The separate score
using bandwidth-matched iMAR had 3.61 mm/s² median error with the
position method. That measurement used logged gyro rates to align
the vectors, so it is separate from the two gyro-free measurements.
[Bandwidth comparison](ESA_GIRAFE_FORCE_BANDWIDTH_RESULT.md)

With each position's reported covariance propagated through the
derivative, the median uncertainty in an individual force prediction
was 1.45 mm/s² for independent epochs, 0.79 mm/s² for 30-second
correlation and 0.0035 mm/s² for fully shared errors. These are working
scenarios. They hold the center and reference height fixed and
leave the actual correlation of receiver errors open.
[Velocity error scenarios](ESA_FORCE_VELOCITY_ERROR_RESULT.md)

All eight tasks passed the derivative and accounting checks. The
study scored previously recorded data on one development flight.
It used zero original recording reads or protected flight groups.
[Frozen design](ESA_FORCE_POSITION_DERIVATIVE_PLAN.md) ·
[Complete scores and charges](esa-force-position-derivative-result.json)

To verify the saved result, restore
`data/esa-force-position-derivative-v1` and run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_force_position_derivative report
```
