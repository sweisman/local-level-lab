# What RF04 attitude adds to the force-direction check

With RF04 attitude supplied separately, both globe settings predicted the
later measured accelerometer directions more closely than both disc settings
in each of the four GPS-track and packet-clock combinations. The test used
one constant alignment per model, fitted on the earlier observations. It
compared the same later samples across models within each combination.
[Fixed plan](RF04_FORCE_DIRECTION_PLAN.md)

| GPS track | Packet clock | Later samples | Globe direction error, RMS | Disc direction error, RMS |
| --- | --- | ---: | ---: | ---: |
| Onboard receiver | Nominal 200 Hz | 118 | 1.024° | 1.068° |
| Carrier phase | Nominal 200 Hz | 118 | 1.023° | 1.067° |
| Onboard receiver | Elapsed header time | 19 | 0.852° | 0.923° |
| Carrier phase | Elapsed header time | 19 | 0.853° | 0.923° |

Values in each model family round to the same number at the precision
shown for both background-field settings. Each comparison used 265 earlier
samples. The clock choices retained different later samples under the
5 ms tolerance. The lower errors on the header-clock subset do not
establish that clock as more accurate.

The largest later RMS separation between any two model predictions was
0.368° before their earlier alignments and 0.288° afterward. These
separations are smaller than the observed direction errors. The ranking
describes this single flight with RF04's fused attitude and the saved
trajectory estimates supplied. It leaves the adequacy of the single-packet
force model and the acceleration-only shape question open. A follow-up can
compare force averages on the same timestamps across both packet clocks.
[Independent limitations and timing](RF04_MOTION_MATCH_RESULT.md)

The task completed 16 direction comparisons and 24 pairs of predictions
under all 41 charged operations. Six focused tests passed. The calculation
reused saved force inputs and used zero original IMU decodes, new
Earth-model fits or reserved ESA reads. [Saved metrics and receipt](rf04-force-direction-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_rf04_force_direction report
```
