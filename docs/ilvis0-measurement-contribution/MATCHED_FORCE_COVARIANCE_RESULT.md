# Shared GPS errors mostly cancel in the predicted shape difference

The same assumed receiver error was propagated through all four predicted
force means on the 991 saved windows. The table gives median standard
deviations under the nominal clock, in m/s².

| Recorder | One candidate's force | Globe–disc difference, zero field | Globe–disc difference, specified field |
|---|---:|---:|---:|
| IMU8 | 0.01355 | 0.000330 | 0.000296 |
| IMU21 | 0.01355 | 0.0000373 | 0.0000497 |

The four absolute-force columns round to the same value on each recording.
Comparing two model predictions cancels much of the GPS error because the
same position errors affect both. Choosing which prediction matches the
accelerometer still depends on the larger absolute-force uncertainty.

Ignoring overlap changed the uncertainty of the training and later means.
Under the nominal clock, the conditional standard deviation of the mean
shape difference was **1.29–3.41 times** the independent-window calculation.
For the mean absolute forces the multiplier ranged from **0.56 to 1.06**.
Correlated errors can cancel in a mean as well as reinforce it.

The largest later onboard IMU8 lower-bound violation after applying the
training gain was **0.224** of its projected standard deviation. IMU21 had
none at those settings. These scales come from the assumed receiver law.
They supply no p-value or calibrated aircraft coverage.

The [frozen projection](MATCHED_FORCE_COVARIANCE_PLAN.md) uses the onboard
GPS stream, both clocks and the original split. The linear drift is scaled
over each complete recording. The calculation keeps the shared errors
in each window and in the full covariance of the training and later means.
The aircraft error law, nonlinear coverage and joint instrument calibration
remain open. The gyro-free comparison continues to abstain.

[Window table](matched-force-covariance-windows.csv.gz) · [Covariance receipt](matched-force-covariance-receipt.json).

Restore the [prepared inputs](MATCHED_FORCE_SUPPORT_RESULT.md) if needed, then replay with

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_force_covariance replay
```
