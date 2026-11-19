# Bound the ESA calibration map over smaller attitude ranges

Keep the two forecasts, earlier GPS score, 174 prior constraints and
calibration parameter limits from the
[bias and force product check](ESA_ACCELERATION_PRODUCT_SCORE_RESULT.md).
Use the original 0.01 limit on earlier loss increase and the 0.1 working
allowance for earlier unshared error. This tests the wider of the two
preceding earlier-error scenarios.

Bisect vertical-axis attitude, then bisect each of the other two attitude
coordinates in both halves. Keep the eight closed ranges and all shared
boundaries. Verify their union against the original box before scoring.
In each range, construct and audit 48 additional inequalities for
the complete static map, using the original source, caps and normalized
allowance. Every physically linked example inside a range must still
satisfy its constraints.

Per range, allow one direct proposal of up to 200 iterations, one linear
proposal at its tangent and two exact certificates. One certificate
reuses the whole-box direction and weights on the narrower range.
Use the smallest checked upper bound, including the original whole-box
upper bound, and retain the maximum across all eight ranges.
An unsuccessful solver status alone cannot exclude a range.

Allow sixteen charged range calculations of 17 steps across two
one-thread workers, with a 150-second cooperative wall limit.
No trajectory fits, withheld receiver positions or reserved recordings
are used. The static-map allowance, full integrating model's unshared
error and flight-level prediction uncertainty remain separate premises.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_attitude_cover_score
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-attitude-cover-score-v1-20261119 --reserved-threads 0
```
