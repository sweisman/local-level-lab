# Receiver predictions sealed for eight new ESA windows

All eight [selected windows](ESA_DIRECTION_HOLDOUT_SELECTION_RESULT.md)
have complete one-second receiver reports. The [prediction plan](ESA_DIRECTION_HOLDOUT_FORECAST_PLAN.md)
uses 400 reports per window from one GNSS receiver. Both shapes have
predictions for 28 angles in each averaging, differentiation and field
setting. All 5,376 angles are finite. No new inertial data were read.

The previous eight windows set 24 error references ranging from 0.010°
to 0.129° RMS. These describe the earlier accuracy, including the effect
of the antenna correction. The next check compares the new inertial
angles with the predictions and measures whether this accuracy transfers
within recording 187. Independent flight accuracy remains open.

The [sealed receipt](esa-direction-holdout-forecast.json) has SHA-256
`11a7e455490dff5b980d382edd035ea70c3adec71da2d5efe6c13a726734f5f9`.
Manifest SHA-256 is
`0a2b634635e4b13b87795e126135797ab193c3dcd13c0981838c5de9fd689caf`.
The task passed with 17 charged checks, 238,160 charged steps and zero
navigation fits. It completed in 6.1 seconds on one numerical thread.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_forecast prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-forecast-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_forecast report
```
