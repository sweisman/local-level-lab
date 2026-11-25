# Turning matches closely once the time difference is allowed for

The [first comparison](MOTION_MATCH_RESULT.md) found the aircraft record
and the instrument about 0.4 s apart along the track, and only a loose
match in turning from second to second. Moving the gyro windows later by
that time difference tightened the match on all 32 stretches. The
one-second difference fell from a median of 0.058° to 0.014°.
[Fixed plan](MOTION_LAG_PLAN.md) · [Per-stretch table](motion-lag.csv)

No globe or disc model was evaluated.

| Window | Turning in the window | Difference, no shift | Shifted by the GPS lag | Shifted by 0.49 s |
| --- | ---: | ---: | ---: | ---: |
| 1 second | 0.096° | 0.058° (0.027 to 0.168) | 0.014° (0.009 to 0.038) | 0.012° (0.006 to 0.031) |
| 5 seconds | 0.255° | 0.084° (0.057 to 0.189) | 0.031° (0.022 to 0.053) | 0.028° (0.020 to 0.050) |
| 10 seconds | 0.291° | 0.089° (0.063 to 0.174) | 0.051° (0.034 to 0.090) | 0.050° (0.033 to 0.088) |

Each cell is the median RMS across the 32 stretches, with the smallest and
largest in brackets. The GPS lag is each stretch's own value from the first
comparison, 0.39 to 0.45 s. The 0.49 s shift is the middle of a one-second
average of 50 samples. All three shifts were fixed before the rotation data
were compared. The table uses the recorded packet clock.

- Both shifts lowered the difference on all 32 stretches at all three
  window lengths.
- Over one second, the difference fell from 57% of the turning to 15% with
  the GPS lag and 12% with the 0.49 s shift.
- The 0.49 s shift gave a lower difference than the GPS lag on all 32
  stretches at one second and at ten seconds.
- With no shift, the figures repeat the first comparison.

## What this does and does not show

The result supports the reading that the aircraft file labels each
one-second average with the start of its second. On that reading the two
systems recorded the same turning, and most of the earlier mismatch was a
difference in time labels. The comparison does not show which label is
right, and it sets no limit on motion inside a second.

What remains grows with the length of the window: 0.012°, 0.028° and
0.050°. The aircraft's navigation system reports orientation relative to
the ground below it, and the gyros measure rotation directly, so a steady
difference between the two is expected. This comparison does not measure
it. It is not evidence for any Earth model, because the aircraft's
navigation system is itself built on globe equations.

Thirty-two tasks completed all 640 charged calculations with zero
Earth-model fits. Three focused software tests passed.
[Saved metrics and receipt](motion-lag-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_review_checks_report motion-lag
```
