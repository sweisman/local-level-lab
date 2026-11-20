# The saved forecast ranking survives the spread between GPS solutions

On both recordings, the specified-field globe forecast had smaller
horizontal and height errors than the specified-field disc for every
reference within the three-solution GPS hull. This held at 30, 60 and 120
seconds and over the full saved forecast. Each comparison uses one common
reference for both models. Its position can move within the hull at every
epoch.

| Recording | First 30 s, extra horizontal error needed for a tie | Full forecast, extra horizontal error needed for a tie | Full forecast, smallest globe horizontal RMS | Full forecast, smallest globe height RMS |
|---|---:|---:|---:|---:|
| IMU8, 223 s | 12.06 m | 159.49 m | 19.19 m | 10.45 m |
| IMU21, 148 s | 2.38 m | 49.66 m | 2.03 m | 4.80 m |

The tie radius is the smallest extra displacement allowed at each epoch
that could erase the mean squared-error ordering. It is a sensitivity
measure, not an estimate of actual GPS error. The same pair's full-forecast
height tie radii were 21.29 m and 6.07 m. The specified-field globe also
outscored the zero-field globe at each horizon. The zero-field disc
forecast is missing on both recordings, so the overall four-model
comparison stays open.

The lower RMS limits show how much disagreement remains even when the
reference can move freely within the measured receiver spread. They leave
unknown errors common to all three GPS solutions outside the calculation.
This check replays saved results from two retrospective development
recordings. It establishes no calibrated prediction range or positive
scientific decision.

[Frozen plan](MATCHED_FORECAST_RECEIVER_PLAN.md) · [All horizons and ranks](matched-forecast-receiver-receipt.json) ·
[Saved forecast evidence](../ilvis0-matched-observed-preflight-runtime/README.md).

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_forecast_receiver replay
```
