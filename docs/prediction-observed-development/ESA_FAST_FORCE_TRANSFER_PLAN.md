# Test fast force variation against sealed ESA position errors

Reuse the two 120-report forecasts from the [native transfer check](ESA_NATIVE_ROLLING_TRANSFER_RESULT.md).
For each receiver interval, use the recorded acceleration vectors to
calculate the reduction in mean force magnitude when vectors are averaged
in 0.1-second bins first. Use exactly the preceding receiver interval and
the original timestamps. Report this effect and the archived position
and innovation errors in the same four 30-report blocks per forecast.

Test three ways to scale every original three-component innovation:
equal variance, variance increasing with fast force variation during the
current interval, and variance increasing with the 15-second causal
exponential average of the variation. The two varying multipliers add
one to measured variation divided by the earlier median, floored at
0.001 m/s² for the divisor. Fix the reference and fit one positive common
variance scale per arm using the earlier forecast. Commit those values
to a separate receipt before scoring the later forecast. Compare proper
Gaussian log scores including the variance normalization, along with the
squared standardized error. A larger variance is penalized even where
it lowers the squared standardized error.

The two phases each permit one source hash pass, at most 40,000 decoded
IMU samples, 120 variation calculations, six score evaluations under two
archived IMU error descriptions and one numerical thread. No replacement
model fits, native propagation or reserved groups enter this check.
These are retrospective diagnostics on one previously scored flight. The
comparison cannot identify a causal effect or establish future coverage.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_fast_force_transfer freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_fast_force_transfer earlier
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_fast_force_transfer compare
```
