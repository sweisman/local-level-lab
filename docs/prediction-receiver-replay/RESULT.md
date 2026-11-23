# Saved forecasts can be scored against simulated receiver readings

All 24 archived forecasts for the first calibration seed were rescored
without running a fit. For every replay, the original 79 receiver readings
used for fitting and their injected errors matched the saved hashes. The same
seeded process then supplied 40 noisy readings for comparison with each saved
forecast. This check used one seed, zero aircraft recordings and zero cases
from the original validation cohort.

| Comparison over the 40 withheld positions | 3D RMS range across saved fits |
| --- | ---: |
| Forecast against exact simulated positions | 2.503–3.009 m |
| Same forecast against simulated receiver readings | 2.675–3.142 m |
| Simulated receiver readings against exact positions | 0.715 m |

The raw forecasts were integrated without later GPS input. These metre-scale
errors use a common 3D position measure; the original calibration used a
different, normalized score based on forecasts adjusted with training data.
Each of the 24 fits used its own generating model. The replay therefore tests
the input recovery needed for a new reference score. Estimating discrimination
still requires matched three-model predictions, a relevant aircraft error
model and independent validation of the new target and score.

[Replay instructions](README.md) · [Frozen inputs and sources](freeze.json) ·
[Per-fit records](result.json).
