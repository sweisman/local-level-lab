# Can a persistent heading error reproduce the forecast miss after the turn?

Use the original two 120-report receiver-conditioned forecasts on ESA
development recording 187. The exploratory hypothesis is that an angular
offset lasting after the observed turn would accumulate cross-track error.
Fix the step immediately after the 60th forecast report on both paths.
This is the end of the reported turn block in the later path. It is a
placebo at the same forecast age in the earlier path.

Use the sealed predicted positions to compute the first-order horizontal
deflection from a fixed heading error. The deflection is perpendicular
to the horizontal predicted displacement from the step epoch. Keep
the height path unchanged. Project the original errors onto the one
declared error direction using the full archived conditional receiver
covariance. Estimate the best step retrospectively without imposing
an instrument-specific bound. This gives an upper limit on what this one
direction can explain, assuming the archived error law.

There are four fixed one-dimensional projections, two at each origin.
There are no optimizer starts, native sweeps or reserved flight reads.
The comparison cannot identify a physical sensor error or qualify a new
forecast rule.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_heading_step freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_heading_step replay
```
