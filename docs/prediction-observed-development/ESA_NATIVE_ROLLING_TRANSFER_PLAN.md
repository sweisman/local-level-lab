# Verify whether native forecast error transfers between the two ESA cuts

Use the earlier and later 120-report forecasts already sealed on ESA
development recording 187. The cuts are at reports 200 and 400. Use
the same specified-field model with no removal for both origins. Keep
both IMU error descriptions, one for recorded increments and one for
sampled rate points. All four fitted calibrations stay fixed.

Rebuild just the archived covariance operation and save its numerical
factors. Require the same covariance identity, earlier cost and
determinant, and identical conditioned means and marginal covariance.
The workers accept only observations before each cut and the original
IMU stream. After closure, compute a joint conditional score for the
120 earlier held-out reports and seal it. Then verify and score the
original 120 later reports. Compare the average squared standardized
errors for the same law at both origins.

The four tasks use four one-thread workers and a 600-second cooperative
wall limit. Each permits one bridge build and at most one noise call
per packet plus one per query. No fit restarts or protected-flight
reads are authorized. The finite [qualified recovery procedure](ESA_ORIGINAL_WHITENING_PLAN.md)
applies with this study ID, 1,200 seconds for the recovery campaign and
up to four interrupted identities. Each unfinished identity has a limit
of two starts. The earlier and later holdouts are disjoint windows from
the same flight. The earlier holdout was available to the later fit.
The result describes forecast error on this flight and leaves aircraft
coverage and decision limits open.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_native_rolling_transfer prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-native-rolling-transfer-v1-20261118 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_native_rolling_transfer score-earlier
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_native_rolling_transfer score-later
```
