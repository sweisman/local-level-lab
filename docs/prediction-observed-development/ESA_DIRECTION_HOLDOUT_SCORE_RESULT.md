# Testing predicted angles on eight further ESA windows

Seven windows gave the globe a smaller angle error at every tested
setting. The strongest turn, on the second flight leg, depended on how
the background field was represented. Both shapes were scored against the
same recorded inertial measurement unit (IMU) data. The [receiver predictions](ESA_DIRECTION_HOLDOUT_FORECAST_RESULT.md)
were sealed before those measurements were read.

| Background field setting | Globe lower error | Disc lower error | Globe within earlier error reference | Disc within earlier error reference |
| --- | ---: | ---: | ---: | ---: |
| Zero | 56/64 | 8/64 | 55/64 | 40/64 |
| Specified field retained in the gyro | 64/64 | 0/64 | 63/64 | 17/64 |
| Specified field removed from the gyro | 60/64 | 4/64 | 64/64 | 40/64 |

Each row repeats eight windows at two averaging widths, with two receiver
differentiation methods and with or without the antenna correction. The
error reference is the worst of the eight closest-model errors in the
earlier windows for the same setting. It describes how closely earlier
predictions matched measured angles. In the new windows, both shapes
exceeded it in two settings. The test uses one instrument installation,
and multiple settings applied to the same window share data.

## What changed on the turn

The lone receiver-labeled turn starts at query 51976. Each cell below
gives the median of eight RMS angle errors in degrees.

| Background field setting | Globe | Disc | Lower error on the turn |
| --- | ---: | ---: | --- |
| Zero | 0.1703° | 0.0800° | Disc in 8/8 |
| Specified field retained in the gyro | 0.0123° | 0.2032° | Globe in 8/8 |
| Specified field removed from the gyro | 0.1044° | 0.1051° | Globe with the antenna correction and disc without it |

The specified field enters both shape predictions in the retained-field
comparison. The turn shows why motion and field assumptions matter when
testing shape this way. Under the removal setting, changes as small as
0.0015–0.0042° RMS in the observed angles would tie the scores on this turn.
Across all retained-field settings, the median errors were 0.0040° for
globe and 0.0412° for disc. This is a prediction check on one recording.
Independent-flight uncertainty and a scientific decision remain open.

As a separate check of the saved scores, let each shape use its lowest
error among the three tested field settings. The globe has the smaller
error in all 64 matched comparisons, including eight on the turn.
On the turn, the best disc score uses zero field and the best globe score
uses the retained field. The difference is 0.065–0.073° RMS. This comparison
covers the three settings tested. Intermediate field strengths and an
independent accuracy standard remain open.

## Reproduce the check

The [plan](ESA_DIRECTION_HOLDOUT_SCORE_PLAN.md) specifies the source,
measurement construction and score. All eight sensor windows passed the
fixed-length and continuity checks. They contain 957,841 raw sample
intervals including edge padding, with a largest gap of 3.334 ms.
The original file hash matched. The study used nine charged operations and
zero fits, finishing in 52 seconds on one numerical thread. The seven
reserved flight groups remain unopened.

The [score receipt](esa-direction-holdout-score.json) records all 192
comparisons and the measured angles. Its SHA-256 is
`d151cfceb38de59035ec26e53a217c4a9b3dec2fefe50a1e0143166dbdd6313e`.
Manifest SHA-256 is
`d5bf1c715aabde54ff289724fcd4e12ef108d34becd93fc6e4c65a8bb7c67dc9`.

The frozen inputs, calculation and charge records are in the repository's
evidence archive. [Initial selection attempt](esa-direction-holdout-evidence/selection-initial/evidence-receipt.json) ·
[Selection](esa-direction-holdout-evidence/selection/evidence-receipt.json) ·
[Receiver predictions](esa-direction-holdout-evidence/forecasts/evidence-receipt.json) ·
[Measured-angle scores](esa-direction-holdout-evidence/scores/evidence-receipt.json)

Portable copies contain the same frozen evidence and can be verified without
loading the shared catalog. [Initial selection](esa-direction-holdout-evidence/selection-initial/bundle.zip) ·
[Selection](esa-direction-holdout-evidence/selection/bundle.zip) ·
[Predictions](esa-direction-holdout-evidence/forecasts/bundle.zip) ·
[Scores](esa-direction-holdout-evidence/scores/bundle.zip)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_score prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-score-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_score report
```
