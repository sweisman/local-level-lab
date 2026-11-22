# Separate aircraft error scales on known-answer data

The [motion preflight](ESA_COMPONENT_PREFLIGHT_RESULT.md) identified two
different error patterns in saved forecasts. A single multiplier for both
transferred poorly. The next software check estimates one scale per
covariance component and can abstain when those components have the same
effect or when a quiet interval contains no maneuver information.

## Implementation and checks

1. Add a small dense reference estimator in
   `analysis/lll/covariance_scale_fit.py`. Each input is a group of
   independent forecast-error draws with the same covariance design. A
   single observed flight would enter as a joint residual vector so that
   receiver epochs and overlapping windows do not count as independent.
2. Reject absent or linearly dependent covariance terms before fitting.
   For the full-rank controls, minimize the Gaussian negative log
   likelihood over specified log-variance bounds with a fixed evaluation
   cap. Report numerical failure or a bound hit separately from an interior
   fit. The calculation assumes a fixed mean forecast.
3. Verify an exact diagonal case and a generated correlated case with
   quiet and maneuvering designs. Include an entirely quiet design and
   a design with confounded terms. Use a separate generated ensemble to
   check forecast scores in the correlated case.

These are small deterministic software tests using one numerical thread.
They use no recording, trajectory fit, or reserved data. They do not set
aircraft error ranges, establish coverage, or authorize opening any new
flight groups.

## Result

All six checks passed. The estimator recovered the exact diagonal
answer to within 0.001% and the three correlated-case variances to
within 10%. On a separate generated sample, the three fitted scales
outscored a common multiplier in both the quiet and maneuvering cases.
The entirely quiet and confounded cases both abstained without any
optimization. The two remaining checks verify that the calculation
reports a bound hit and stops at its evaluation allowance.

This comparison uses generated independent error draws and known mean
forecasts. The next check needs to include uncertainty in the fitted
flight parameters and preserve error dependence across the training cut.
It should also test what happens with few independent trajectories,
where wide or unsupported estimates may be appropriate.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_covariance_scale_fit.py
```
