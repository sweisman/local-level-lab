# How much shape separation depends on the start of the forecast?

The [matched path check](MATCHED_SHAPE_DRIFT_RESULT.md) found about 0.76 m RMS
of separation outside smooth path differences. Test whether the corresponding
covariance-weighted difference depends on the first few forecast reports.

Use both complete settings of the [saved ESA comparison](FORECAST_PAIR_INFORMATION_RESULT.md).
Use the training-selected zero-field globe and disc means, the two drift
covariances and both earlier receiver weighting rules. Keep the training
cut fixed. Compare the complete later paths and omit the first 1, 5, 10 or
20 later reports. In each case recalculate the difference left after removing
a quadratic term on each axis.

Use the marginal covariance of the retained later reports given the training
data. Form it by taking the corresponding rows of the original conditional
covariance factor. This allows the omitted reports to remain unknown. Using
only the trailing block of the original whitening factor would instead
condition on those reports.

The complete-period distance must match the earlier quadratic comparison.
In a correctly weighted calculation, dropping reports cannot make this
distance larger. The test describes the location of separation in the saved
forecast means. It uses no later positions and establishes no aircraft
accuracy or rejection threshold.

Use one numerical thread, four covariance operators and at most 40 small
projections. Read only the two checked sets of conditional means and earlier
weights from the existing study evidence. Start no fits and open no original
or protected recordings.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_forecast_boundary freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.shape_forecast_boundary calculate
```
