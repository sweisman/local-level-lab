# Dependence in the ESA development forecasts

This check reads the 22 sealed forecasts from one development
recording. It makes no new fits and reads no reserved confirmation
group. The two unfinished original fits remain visible in the
[per-fit table](error-structure.csv).

The table reports median correlation of later prediction errors
across the 22 fits. The last two columns remove each fit’s
straight-line trend first. This describes the errors;
it does not fit or validate a covariance law.

| Direction | Raw, 1 epoch apart | Detrended, 1 epoch apart | Detrended, 60 epochs apart |
|---|---:|---:|---:|
| North | 0.999999 | 0.999814 | 0.351311 |
| East | 1.000000 | 0.999813 | 0.362469 |
| Height | 1.000000 | 0.999811 | 0.360652 |

The next table compares later forecast RMS with the RMS of
residuals from the earlier period used to fit each model. It is
the median ratio across completed settings of the same candidate.
The earlier residuals are **in sample**; these ratios are a
diagnostic of forecast growth, not uncertainty multipliers.

| Candidate | Forecasts | North | East | Height |
|---|---:|---:|---:|---:|
| Globe + specified field | 8 | 97.9× | 177.9× | 83.8× |
| Globe + zero field | 8 | 11.7× | 21.9× | 25.3× |
| Tested flat disc | 6 | 8.5× | 18.1× | 16.5× |

On this development recording, a fixed forecast-error scale
taken from the fitted training residual RMS would miss the
large growth during prediction. The ratios do not identify
which instrument or motion error caused that growth.

The median receiver gap is 1.000002 seconds;
every gap lies within 0.002 seconds of one second. Thus one
and 60 epochs correspond approximately to one and 60 seconds.
Each fit has 400 later receiver epochs. Those
epochs share the same earlier fitted calibration and IMU
forecast; they are not 400 independent trials. Trend removal
is diagnostic, not a model correction or coverage claim.
A usable aircraft error law still needs training-only estimation
and independent prediction checks.

[Receiver precision comparison](README.md) ·
[Prediction uncertainty roadmap](../PREDICTION_ERROR_LAW_PLAN.md)
