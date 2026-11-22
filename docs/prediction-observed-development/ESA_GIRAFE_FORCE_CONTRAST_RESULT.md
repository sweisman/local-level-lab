# Force magnitude alone leaves shape unresolved on the ESA flight

Across eight windows, the predicted difference between globe and disc
was smaller than both the difference between the two instruments and
the largest change from switching receiver products, in every tested
setting. The comparison uses raw iMAR acceleration and separate
GIRAFE measurements. Neither logged iMAR gyro rates nor fused attitude
enter the scores.

| Background field used for both shapes | Predicted globe–disc difference, median RMS | Range | Settings exceeding both observed comparisons |
| --- | ---: | ---: | ---: |
| Zero field | 0.028 mm/s² | 0.008–0.657 mm/s² | 0 of 96 |
| Specified field | 0.026 mm/s² | 0.008–0.645 mm/s² | 0 of 96 |

The two sensors differed by **1.85 mm/s² RMS at the median**. The
largest change from swapping receiver products in each setting had
a median of **0.92 mm/s² RMS**. These values use the same earlier-only
offset removal as the shape comparison. The receiver comparison uses
three products from a shared antenna. It does not estimate common
receiver error or separate the errors of the two instruments.

| Background field | Globe lower error using GIRAFE | Globe lower error using iMAR | Sensors disagree on the lower-error shape |
| --- | ---: | ---: | ---: |
| Zero field | 63 of 96 | 52 of 96 | 35 of 96 |
| Specified field | 48 of 96 | 45 of 96 | 33 of 96 |

Each row covers eight windows, two averaging widths, three receiver
products and two gravity assumptions. The scores describe this one
flight. The counts share measurements and have no calibrated decision
threshold. The much stronger direction comparison retains the turning
information measured by the gyro. [Gyro direction comparison](ESA_DIRECTION_LEVER_ARM_RESULT.md)

All eight windows have verified scores. Four straight-course windows
come from the scalar run, three turning windows from the batched run,
and the last window from the support-charged run. The final window
finished in 1.93 seconds. The failed accounting attempt and two time
limits remain in the evidence. The combined ledger charges 443,400
quadrature points, including 25,608 from the two interrupted runs.
[Frozen design](ESA_GIRAFE_FORCE_CONTRAST_PLAN.md) ·
[Accounting failure](ESA_GIRAFE_FORCE_CONTRAST_ACCOUNTING.md) ·
[Batched run](ESA_GIRAFE_FORCE_CONTRAST_BATCH.md) ·
[Final window](ESA_GIRAFE_FORCE_CONTRAST_LEDGER_BLOCK.md)

The [saved table](esa-girafe-force-contrast-result.json) contains
the measured and predicted magnitudes and all scores. To verify it
against the sealed records, restore
`data/esa-girafe-force-contrast-v2`, `data/esa-girafe-force-contrast-v3`
and `data/esa-girafe-force-contrast-v4`, then run this command.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_girafe_force_contrast report
```
