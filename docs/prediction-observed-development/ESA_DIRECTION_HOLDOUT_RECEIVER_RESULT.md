# The direction comparison across three receiver exports

Both alternate receivers reproduced the globe preference on every matched
comparison. The four first-leg windows had complete matches in both
exports. The four second-leg windows had no matches within 2 ms, leaving
the strongest turn unchecked by this comparison.

| Receiver export | Complete windows | Globe lower error across the full field range | Smallest gap between shape error bounds | Largest change from `air1` in the fixed predicted angles |
| --- | ---: | ---: | ---: | ---: |
| `mosaic03` | 4/8 | 32/32 | 0.0282° | 0.00840° RMS |
| `pwrpak7` | 4/8 | 32/32 | 0.0263° | 0.00901° RMS |

Every comparison uses the same measured angles. The continuous field-range
check lets each shape use zero physical field or the specified field with
any fraction retained in the gyroscope. The last column compares the
predicted angle vectors at the three original field settings with the
primary export's predictions. Its values describe sensitivity to processing
choices on the matched windows. The three receivers share one antenna,
so errors common to those outputs remain unmeasured.

## Why the second leg is missing

The primary receiver queries were close to whole GPS seconds on the first
leg and close to half seconds on the second. The 2 ms matching rule found
400 matches per first-leg window and zero per second-leg window. Both
tasks ended without qualifying full coverage. Their valid comparisons and
the four missing windows from each task are retained. A separate clock
check will test a whole-second selection within the same second-leg cells.

## Reproduce the check

The [plan](ESA_DIRECTION_HOLDOUT_RECEIVER_PLAN.md) binds the original
receiver exports to the earlier source audit and the sealed angle receipts.
Both receiver files matched their byte counts, hashes and row-count audits.
The run used 20 charged operations, 68,246,268 charged steps and zero fits
in 50 seconds on one numerical thread. The seven reserved flight groups
remain unopened.

The [receipt](esa-direction-holdout-receiver.json) has SHA-256
`b13af0607e59659f65596ce8e9f032f480eba0539ef958205984ed9e6056c3db`.
Manifest SHA-256 is
`3efeedc63134844c56a4ecf97439a156d9cf282716c6d1f177d2f44c31e8140b`.
The [portable evidence bundle](esa-direction-holdout-evidence/receiver/bundle.zip)
contains the frozen inputs, source, charges and both coverage outcomes.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_receiver prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-receiver-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_receiver report
```
