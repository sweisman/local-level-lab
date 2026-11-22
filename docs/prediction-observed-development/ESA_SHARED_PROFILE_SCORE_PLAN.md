# Score the shared calibration terms jointly

Use the fixed 3 cm receiver covariance and signed shape direction from
the [exact witness replay](SHAPE_REMAINDER_WITNESS_RESULT.md). Use the adjoint
weights over the whole timeline, including the earlier reports that
condition the later score. Sum signed contributions for each of the 24
shared coordinates before taking its magnitude. Compare with the upper
bound that would let the same coordinate vary independently at each report.

This check reads the [frozen coefficient profiles](ESA_SHARED_PROFILE_PLAN.md).
It permits one adjoint calculation and six projections covering the three
blocks of shared terms for each candidate. The calibrated prediction
claim and the earlier fit-loss check remain open.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shared_profile_score \
  --manifest-sha256 80e3e13b8b7850b04d6c93f2cd3d033e337056b3bd59c5fab3b342728f64185b
```
