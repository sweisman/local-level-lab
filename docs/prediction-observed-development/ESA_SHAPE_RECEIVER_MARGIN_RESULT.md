# How much receiver error could change the matched-field result?

With the two forecasts and their weights held fixed, a coordinated
receiver error of **4.43 cm per coordinate** can reverse the shape score
for the original ESA export. For the GPS L1-only path, **0.68 cm per
coordinate** is enough. These are the smallest bounds for the tested
family where errors can move independently between reports. They describe
how sensitive the score is to a worst-case error pattern.

| Allowed receiver error pattern | Original export | GPS L1-only path |
| --- | ---: | ---: |
| Position change at any report, per coordinate | 4.43 cm | 0.68 cm |
| Same position change, only after the training cut | 4.45 cm | 0.68 cm |
| Four-block acceleration change, per component | 0.00773 m/s² | 0.00119 m/s² |
| Later position RMS of that acceleration witness | 27.20 m | 4.19 m |

The acceleration test starts with zero position and velocity correction
before the later reports. It permits four constant accelerations that
join continuously in position and velocity. The much larger position
changes in these examples show why the timing of a receiver error
matters. The square-error comparison already allows smooth position,
velocity and acceleration terms. Rapidly varying corrections can align
more closely with the part of the score that remains.

The calculation maps position changes into the archived score with a
backward pass through the same covariance operator. Outward rounding
gives a lower bound on the change needed to tie. Explicit forward
replays crossed the tie for the two listed paths within 0.1% of each
bound. The other six receiver paths have their bounds in the saved
table. No instrument fixes, new fits or forecast propagations were used.

This checks one fixed same-field comparison on recording 187. The prior
GPS processing checks all preserved its shape preference. To establish
robustness beyond those checks, the receiver error model must limit the
errors that can align with the shape score, including their time
dependence. These thresholds give that qualification a concrete scale.
The independent ESA flights remain sealed.

## Reproduce the calculation

With the archived shape direction and the prior matched receiver score,
run these commands from the repository root in the frozen environment.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_receiver_margin freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shape_receiver_margin calculate
```

[Fixed method](ESA_SHAPE_RECEIVER_MARGIN_PLAN.md) ·
[Source and input freeze](esa-shape-receiver-margin-freeze.json) ·
[Bounds and score reversals](esa-shape-receiver-margin-result.json)
