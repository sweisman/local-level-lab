# A correct ranking can hide error in the distinguishing directions

Three forecasts differ in at most two directions. The other directions
contribute the same squared error to all three scores. Separating these
parts preserved all 56 saved rankings and showed where the working
covariance was too narrow or too wide.

In the twelve generated cases, the reduced-drift law with reported
receiver covariance ranked the correct model first every time. Even so,
its error in the two distinguishing directions exceeded the upper
nominal limit in **10 of 12** cases. The full law with the same receiver
weights ranked the correct model first in 11 of 12 cases and exceeded
that limit in **2 of 12**.

| Error assumptions | Correct model ranked first | Correct model above nominal contrast limit | Common error inside nominal band |
|---|---:|---:|---:|
| Full drift, fixed 3 cm weights | 9/12 | 11/12 | 0/12 |
| Full drift, reported precision | 11/12 | 2/12 | 10/12 |
| Reduced drift, fixed 3 cm weights | 10/12 | 12/12 | 0/12 |
| Reduced drift, reported precision | 12/12 | 10/12 | 9/12 |

The nominal limits are the central 95% chi-square bands for two contrast
directions and 118 remaining directions. They are reference values for a
known Gaussian forecast. Fitting the forecast can change the actual
distribution. These twelve cases diagnose that assumption and leave
calibration to a separate study.

For the two complete ESA development settings, the specified-field globe
had 0.26–0.36 squared error in the contrast directions. The zero-field
globe had 512–660 and the disc had 839–1,032. The common squared error
was only 7.0–10.8 across 358 remaining directions, consistent with the
previous finding that the working error range was too wide on this
flight. The original abstentions and numerical failures remain in the
record.

The replay recovered the generated centers from earlier-only forecasts
and checked their original hashes. It used sealed scores for the later
positions. A future calibration needs to check the covariance in the
distinguishing directions and the fit to the rest of the path separately.
All reserved flight groups remain closed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.model_contrast_partition replay
```

[Fixed design](MODEL_CONTRAST_PARTITION_PLAN.md) ·
[Frozen inputs](model-contrast-partition-freeze.json) ·
[All decompositions](model-contrast-partition-result.json)
