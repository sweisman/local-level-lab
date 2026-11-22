# What the ESA scores say about the assumed error scale

On ESA development recording 187, both complete settings still rank the
specified-field globe first. Under the provisional decision rule, it would
also pass the absolute reference check in the two ranges below. The original
scale is 100%, so the original decision remains an abstention.

| Receiver weighting | Shared variance as a fraction of nominal | Shared standard deviation as a fraction of nominal |
|---|---:|---:|
| Reported receiver precision | 0.01774–0.02442 | 13.3%–15.6% |
| Fixed 3 cm receiver weights | 0.02619–0.03575 | 16.2%–18.9% |

The intervals use one multiplier for all models and error assumptions on the
sealed forecasts. Each band lets at least one assumption satisfy the original
physical accuracy and reference checks. There is no common multiplier that
puts both receiver weightings inside the reference band at once. The two
bands show how much the absolute-fit check depends on the error assumptions.
They are sensitivity results and cannot supply a calibrated scale for this
flight.

Across either complete setting, the zero-field globe first becomes compatible
at about 1.26 times the nominal variance and the disc at about 2.04 times.
Compatibility uses the upper reference limit alone. Neither competitor
produces a sole adequate shape or field result anywhere on the common scale
axis. The two incomplete settings remain incomplete.

This replay used the sealed scores. It made no new fit and read no reserved
flight. A common scale change leaves the time correlations and saved fitted
paths untouched. Before using any scale in a decision, justify the covariance
and check how well an earlier-only estimate transfers to later data.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.joint_score_scale_window replay
```

[Fixed scope](JOINT_SCORE_SCALE_WINDOW_PLAN.md) ·
[Frozen inputs](joint-score-scale-window-freeze.json) ·
[Full intervals](joint-score-scale-window-result.json)
