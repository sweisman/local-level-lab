# Fixed calibration-swap result

All 24 declared vectors finished. Each unchanged baseline and
full-vector swap exactly reproduced the corresponding saved training
cost and continuous forecast. No optimizer ran and no later receiver
position entered a calculation. The table shows how far each
one-group swap moves the **later forecast path** from its anchor;
the two numbers are the two swap directions. Training cost is the
weighted squared receiver error on the fitted portion, not metres.

## 2010 northern pair

The two original forecasts differ by up to 0.752 m.

| Swapped coordinates | A toward B path shift | B toward A path shift | Training cost increase |
|---|---:|---:|---:|
| time | 0.001 m | 0.001 m | 4.07e-07–4.09e-07 |
| vertical | 9.594 m | 9.967 m | 3.13–3.38 |
| horizontal | 99.156 m | 99.134 m | 341–341 |
| state mount | 92.797 m | 93.325 m | 294–298 |

The isolated swaps worsen the training fit. Their path shifts
are not plausible alternative forecasts on their own. The
nearly equal costs of the two whole vectors instead show that
calibration groups compensate one another. Their effects need
not add up to the full pair difference.

## 2015 southern pair

The two original forecasts differ by up to 0.320 m.

| Swapped coordinates | A toward B path shift | B toward A path shift | Training cost increase |
|---|---:|---:|---:|
| time | 2.362 m | 2.362 m | 3.56–3.56 |
| vertical | 7.193 m | 7.193 m | 0.165–0.165 |
| horizontal | 302.025 m | 302.046 m | 2.62e+03–2.62e+03 |
| state mount | 299.773 m | 299.788 m | 2.57e+03–2.57e+03 |

The isolated swaps worsen the training fit. Their path shifts
are not plausible alternative forecasts on their own. The
nearly equal costs of the two whole vectors instead show that
calibration groups compensate one another. Their effects need
not add up to the full pair difference.

Training costs and each vector’s remaining distance to the opposite
forecast are retained in the [complete table](observed-calibration-swap.csv).
A forecast shift does not identify the true physical calibration or
make a failed fit pass. The numerical method, aircraft prediction
adequacy and Earth-model decision remain unqualified.

[Frozen plan](OBSERVED_CALIBRATION_SWAP_PLAN.md) · [Timing check](OBSERVED_FIXED_ENDPOINT_RESULT.md)
