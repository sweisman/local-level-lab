# Without the navigation-status flag, the selection gains 16 short intervals

The published selection was repeated on all 232 retained files with one
change: the instrument's navigation computer no longer had to report full
alignment. Every other rule was kept. The scan reproduced all 53 published
stretches exactly and found 16 more intervals, 114.9 minutes in total.
[Fixed plan](PLAN.md) · [The 16 intervals](other-intervals.csv)

No gyro residual was examined and no Earth model was evaluated.

## What the 16 intervals are

All 16 come from one kind of file: a second recorder that flew beside the
main one on the 2011 and 2015 flights. Its files are labelled
`510`, and each is a single recording of about eight minutes. In every one
of these files the navigation computer reported incomplete alignment at
every sample, so the flag removed the whole file. Each file yields one
interval of 5.6 to 7.9 minutes at 712 km/hour or more.

| | Intervals | Minutes |
| --- | ---: | ---: |
| Overlap a published stretch from another recorder on the same flight | 14 | 100.7 |
| On a flight leg with no published stretch (17 October 2011 and 12 October 2015) | 2 | 14.2 |

The 14 overlapping intervals are a second recording of flight time that
the published comparison already covers. They are not additional flights.
The other two add 14.2 minutes of flight time, against 424.3 minutes in
the published 53. The two clocks may differ by several seconds, so the
overlap is established to the minute and not to the second.

## What this means for the published result

The flag did keep data out, and all of it came from one recorder model.
It kept out no other interval in any of the 232 files. The published 53
stretches and their fits are unchanged.

The 16 intervals are candidates only. Their roll, climb and turn-rate
checks came from a navigation solution that never reported alignment, so
they are less dependable than for the published stretches. A
[check from GPS alone](RECEIVER_MOTION_RESULT.md) found 14 of the 16 inside
the range of the published stretches and two just outside on one measure.
Before any is fitted, a fixed rule must still check the information it
carries about every fitted parameter. The 14 overlapping
intervals could also serve as a second recording of the same flight for a
consistency check.

All 232 files were read, with no file rejected. Three focused software
tests passed. [Saved counts and receipt](result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_review_checks_report selection
```

[Review finding S2](../red-team-20261125/README.md#s2-selection-depends-on-the-instruments-own-navigation-status)
