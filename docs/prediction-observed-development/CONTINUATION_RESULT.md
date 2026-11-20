# ESA development continuation: withheld prediction

The separately frozen continuation finished its one task on development
recording 187. It reused the two saved fits, completed the missing receiver
error bound, and scored 400 later receiver positions. It made **no new fit**
and opened none of the seven reserved ESA confirmation groups. The parent
pilot's exhausted allowance and technical failure remain recorded.

| Check | Saved result |
|---|---:|
| Completed tasks | 1 of 1 |
| Training / later receiver positions | 800 / 400 |
| Training horizontal error, either error law | about 40 m RMS |
| Later horizontal error, either error law | about 249 m RMS |
| Later maximum horizontal error | about 390 m |
| Preset training and later horizontal limits | 10 m RMS; 50 m maximum |
| Later receiver readings inside calculated coordinate intervals | 400 of 400 on each axis |

The two error laws give nearly identical forecasts and neither is selected by
the training-only law check. Both forecasts fail the preset horizontal accuracy
limits on training and later positions. The intervals are conditional on an
assumed error-law family and calibration box; their apparent coverage here is
**not** a calibrated success or a substitute for an accurate forecast. Physical
aircraft-position truth is unavailable. The result is **abstain**, with no
Earth-model conclusion from this development recording.

The next gate is to diagnose the horizontal miss from saved training and
forecast artifacts, then qualify any revised prediction method on generated
controls before another observed fit. The seven reserved groups stay closed.
The [saved error-trend audit](DRIFT_AUDIT.md) finds that east error grows by
about 41.6 m/min over the withheld period; it does not identify a cause.

The sealed study is `data/prediction-observed-development-continuation-v1-20261113`.
Its completion binds manifest SHA-256
`2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788`
and summary SHA-256
`1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d`.
The [saved-only reporter](../../analysis/lll/prediction_observed_continuation_report.py)
checks those artifacts without calculating a new fit or forecast.

[Fixed continuation plan](CONTINUATION_PLAN.md) · [parent pilot](DIAGNOSIS.md).
