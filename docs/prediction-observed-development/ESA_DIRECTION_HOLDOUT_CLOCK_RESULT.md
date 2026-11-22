# All four second-leg windows now have matching receiver times

Taking the preceding `air1` report moves each query earlier by half a
second. All three receiver exports now match all 400 queries in each of
the same four flight cells. The largest difference between a selected
primary timestamp and its alternate was 0.802 ms, within the original
2 ms limit. There was no interpolation.

| Original first query | Whole-second first query | `air1` | `mosaic03` | `pwrpak7` |
| ---: | ---: | ---: | ---: | ---: |
| 51976 | 51975 | 400 | 400 | 400 |
| 53656 | 53655 | 400 | 400 | 400 |
| 55336 | 55335 | 400 | 400 | 400 |
| 57016 | 57015 | 400 | 400 | 400 |

The three matched inputs and the primary predictions are sealed. The
inertial angles still need to be checked at the shifted times. This will
test receiver sensitivity on the second leg, including the turn. Each
shifted window shares its flight cell with the earlier comparison, and
the receivers share an antenna.

The [plan](ESA_DIRECTION_HOLDOUT_CLOCK_PLAN.md) uses the same edge guards,
clock tolerance and differentiation rules as the earlier check. The task
used 13 charged operations, 65,403,212 charged steps and zero fits in
7.6 seconds on one numerical thread. It read no new inertial data and used
no reserved flight group.

The [clock receipt](esa-direction-holdout-clock.json) has SHA-256
`d92ab61e055f215c26f0e31650cfd3ddf52030f126b04c993f85a3958ae743e4`.
Manifest SHA-256 is
`442945da20467bdf31e9861c2903ba06ffda242fe4bfe90d2a5a3020cb58d4f7`.
The [portable evidence bundle](esa-direction-holdout-evidence/clock/bundle.zip)
contains the frozen sources, receipts, matched receiver rows and predictions.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_clock prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-clock-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_clock report
```
