# Earlier-only forecast-error transfer

**8/12 settings have qualified fits at both cuts.**
The frozen study returned 34/48 numerically passing tasks
and charged 1294 native calls. These are three
development recordings with repeated clock and processing settings,
not twelve independent flights.

Each inner fit uses the first third of receiver positions and predicts
the next third. A separate, same-source fit uses the first two thirds
and predicts an equal-length final period. Neither fit sees its
scoring positions before its forecast is saved.

| Direction | Median later/earlier RMS |
|---|---:|
| North | 1.01× |
| East | 0.67× |
| Height | 2.42× |

The [complete setting table](result.csv) includes abstentions,
both selected starts, signed errors, maxima, endpoints and
directional RMS in four successive forecast quarters.
The [fit audit](fit-audit.csv) records all 48 starts, including
failed fits and normalized calibration parameters at a bound.
Ratios describe
transfer within these recordings; they are not confidence
multipliers or an Earth-model decision. Failures and task charges
remain in the sealed study.

[Frozen plan](PLAN.md) · [Prediction-error roadmap](../PREDICTION_ERROR_LAW_PLAN.md)
