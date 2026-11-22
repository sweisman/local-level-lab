# How a shared GPS height error affects the force estimates

A hypothetical 10 cm height error shifted individual force estimates by
up to **0.0082 m/s²**. It changed the globe–disc difference much less.
None of the sampled phases reversed that difference when the two shapes
used the same background field.

| Error period | Median peak change in vertical acceleration | Largest force-vector change | Largest change in globe–disc force magnitude difference |
|---|---:|---:|---:|
| 20 seconds | 0.00117 m/s² | 0.00819 m/s² | 0.0000160 m/s² |
| 60 seconds | 0.000914 m/s² | 0.00107 m/s² | 0.00000210 m/s² |
| 120 seconds | 0.000262 m/s² | 0.000273 m/s² | 0.000000533 m/s² |

The derivative calculation used the original window widths and exactly
matched epochs from 11 receiver pairs. It evaluated 919 windows and kept
61 original abstentions. Adding the same test error to both records
preserved all 25,890 paired height differences. The globe–disc comparison
used the same error at the same phase for both shapes. Its sampled change
was at most 0.081% of the corresponding original difference.

These results apply to one family of height errors with fixed windows,
gravity and geometry. The comparison used no recorded inertial data.
It leaves the size of real shared GPS errors, changes of window, and
possible error in latitude, longitude or timing open.

## Receiver inputs available for the next check

A source-hash comparison found no overlap between the six earlier
[GPS-only reconstructions](../ilvis0-position-20261007/README.md) and the
53 selected stretches. However, all 21 files that meet the saved pilot
checks have checked receiver packet envelopes of types `55` and `57`.
The [receiver-only preflight](GPS_RECONSTRUCTION_PREFLIGHT_RESULT.md)
reassembled the measurement records and checked range and orbit support
at every selected epoch. Ten of the 21 receiver
streams were complete in the wider [receiver position inventory](../ILVIS0.md),
which preserved the boundary fragments of the others. A later position
reconstruction could reveal differences due to the onboard processing
while still sharing some satellite and atmospheric errors.

The [per-window ledger](shared-gps-error-windows.csv), [configuration
freeze](shared-gps-error-freeze.json) and [receipt](shared-gps-error-receipt.json)
bind the result to the [fixed calculation](SHARED_GPS_ERROR_PLAN.md)
and the sealed input studies. Run from the repository root using the
frozen dependencies and environment:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_shared_gps_error replay
```
