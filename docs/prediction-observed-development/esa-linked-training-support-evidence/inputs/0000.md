# How much does earlier GPS constrain shared calibration error?

Use the sealed globe and disc forecasts with the same zero background
field on ESA development recording 187. Keep the 27 physical parameters
and all 24 shared remainder coefficients in one 51-dimensional box for
each candidate. A shared coefficient has the same value at every report.
Use the original 400-report training residual and weighting. Score the
predicted changes in the saved shape direction with the fixed 3 cm
covariance and smooth drift term.

Allow the original earlier squared loss to rise by 0.01. Repeat the
support calculation with assumed bounds of 0, 0.1 and 1 on the earlier
unshared error norm in standardized coordinates. These hypothetical
bounds include any discrepancy between the archived affine terms and
the terms used by the nonlinear integrator. This check leaves unshared
later error outside the score limit, and lets the 24 shared coefficients
range independently within their boxes even when the physical model
couples them.

For each candidate, use at most three proposals of 200 iterations.
Certify each proposed direction with an outward evaluation of the
training and forecast coefficients, Cauchy–Schwarz and exact box support.
The certificate holds regardless of the optimizer's stopping status.
Allow one bound call of three support checks per candidate, with
two one-thread workers and a 120-second overall worker allowance.
Use saved inputs only. Start no fits and read no later receiver positions.
The assumptions still require qualification before any aircraft decision.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_linked_training_support
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-linked-training-support-v1-20261119 --reserved-threads 0
```
