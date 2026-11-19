# Test combined calibration changes on three ESA forecasts

Use start zero from the three passing profiled-removal fits with
increment error on the 400/120 recording 187 comparison. Use each
fit's own three weakest training directions. At coordinates within
`1e-8` of a normalized bound, discard outward components and choose
the sign retaining the greater vector length. Require the three
adjusted directions to remain independent.

For each fit, evaluate three individual changes, three pairs and
one triple at each of two sizes. Use the same underlying increments
in each subset so pairwise differences isolate the effect of changing
two quantities together. Scale the largest subset displacement to
0.01 or 0.10 in the normalized parameter coordinates, and reject any
trial that leaves the original bounds. Check the nominal path within
one micrometre against the sealed prediction before comparing paths.

Report the difference between the combined path change and the sum
of separate changes in physical metres, along with pair interactions
and the remaining three-way interaction. Report each fit's own earlier
and later differences. These directions and scopes diagnose nonlinear
coupling. They do not bound every calibration or test model preference.

The freeze permits three tasks of 15 value sweeps, one thread and a
180-second cooperative wall allowance. There are no optimizer starts,
later receiver-position reads or reserved-flight reads.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_mixed_calibration prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-mixed-calibration-v1-20261118 --reserved-threads 0
```
