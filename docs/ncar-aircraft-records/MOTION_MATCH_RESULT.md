# The aircraft's own record follows the same path on all 32 stretches

On every one of the 32 stretches that has an aircraft record, the separate
GPS receiver and navigation system on the aircraft reported the same path
as the instrument, and the same amount of turning. The comparison covered
15,114 seconds. Every second had a GPS report from both systems, and no
part of the comparison failed. [Fixed plan](MOTION_MATCH_PLAN.md) ·
[Records received](README.md) · [Per-stretch table](motion-match.csv)

No globe or disc model was evaluated. The result describes the aircraft's
motion only.

## The two GPS tracks

| Measure, per stretch | Smallest | Median | Largest |
| --- | ---: | ---: | ---: |
| Offset across the direction of flight | −1.01 m | −0.15 m | 0.55 m |
| Instrument position behind the aircraft record | 86.9 m | 98.6 m | 111.9 m |
| The same distance as a time, 2011 (3 stretches) | 0.392 s | 0.394 s | 0.397 s |
| The same distance as a time, 2015 (29 stretches) | 0.438 s | 0.442 s | 0.449 s |
| Difference in height changes, RMS | 0.24 m | 0.80 m | 2.90 m |

Across the direction of flight the two receivers agree to about a metre.
Along it, the instrument's position trails by 87 to 112 m. That distance
grows with ground speed, which ran from 201 to 253 m/s. Expressed as a time
it is nearly constant within each campaign, so it behaves like a difference
in how the two systems label time and not like a fixed distance between
antennas.

The aircraft files state that GPS position was sampled 5 times a second in
2011 and 10 times a second in 2015. A one-second average labelled with the
start of its second would sit 0.40 s late at 5 samples and 0.45 s late at
10. The measured values are 0.39 s and 0.44 s. This fits one-second
averaging in the aircraft file. The comparison cannot confirm that
explanation, and it does not show which system's time label is right.

## Turning

| Window | Aircraft record change, RMS | Gyro change, RMS | Difference, RMS |
| --- | ---: | ---: | ---: |
| 1 second | 0.096° (0.062 to 0.195) | 0.102° (0.064 to 0.211) | 0.058° (0.027 to 0.168) |
| 5 seconds | 0.255° (0.200 to 0.456) | 0.256° (0.199 to 0.464) | 0.084° (0.057 to 0.189) |
| 10 seconds | 0.291° (0.211 to 0.501) | 0.294° (0.219 to 0.505) | 0.089° (0.063 to 0.174) |

Each cell gives the median across the 32 stretches, with the smallest and
largest in brackets. The table uses the recorded packet clock and no time
shift.

The two systems report nearly the same amount of turning at every window
length. Window by window the match is looser. Over one second the
difference is 43% to 96% of the turning itself, with a median of 57%. Over
ten seconds it is 17% to 51%, with a median of 32%.

Moving the gyro windows 80 ms later lowered the one-second difference on
all 32 stretches. Moving them 80 ms earlier raised it on all 32. The GPS
comparison points to a labelling difference of about 0.4 s, which is larger
than either fixed shift. A [follow-up comparison](MOTION_LAG_RESULT.md) at
that lag lowered the one-second difference to a median of 0.014°.

## What this does and does not show

- The stretches were chosen and described with the instrument's own
  navigation unit. On these 32, a second system recorded the same track and
  the same amount of turning.
- The earlier single-flight check is reproduced: flight RF04 again gives
  443 matched seconds, an 89.2 m median separation and a 0.048° one-second
  difference. [RF04 comparison](../ilvis0-measurement-contribution/RF04_MOTION_MATCH_RESULT.md)
- Twenty-one of the 53 stretches have no aircraft record. The 2015 set
  lists no research flight after 22 October, so the nine stretches of 25,
  27 and 29 October are not covered.
- One-second records can miss a turn that reverses inside a second. The
  result sets no limit on fast motion.
- The aircraft's navigation system reports orientation relative to the
  ground below it, and the gyros measure rotation directly. The two are
  not the same quantity, and the differences above may also reflect
  timing and filtering.

Thirty-two tasks completed all 672 charged calculations with zero
Earth-model fits. Four focused software tests passed.
[Saved metrics and receipt](motion-match-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_review_checks_report motion-match
```
