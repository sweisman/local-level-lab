# Earlier GPS errors make the ESA weighted forecast useful on this recording

One 20-minute ESA development recording supplied 800 early GPS positions for
training and 400 later positions for checking. The IMU error law and all fit
parameters were fixed **before** the later positions were opened.

| Forecast for the later GPS reports | Horizontal RMS | Vertical RMS | Preset accuracy screen |
|---|---:|---:|---|
| Uncorrected IMU trajectory | 249.41 m | 4.35 m | Fails |
| Same trajectory, conditioned on earlier GPS errors | **2.85 m** | 11.88 m | Passes |

The early GPS errors reveal how the declared, slowly varying IMU error state
is evolving. Under that declared error law, carrying the estimated state
forward shifts the later horizontal prediction by about 247 m RMS. The
conditional forecast then matches the later receiver reports much more
closely. This explains why the earlier 249 m *uncorrected* trajectory did not
by itself show that the weighted model was unable to predict.

The full error operator was built once from the same saved IMU stream and
training-only initial state. Its early covariance replayed the original
training log-determinant **−60,972.780013550044** and weighted residual cost
**13.236910008550893** exactly. No fit was repeated. The one task completed
in 241 seconds using 361,228 native calls; its source, inputs, environment,
allowance and output are sealed. Thirteen source and recovery checks and five
focused forecast/report checks passed. The [machine report](conditional-forecast-result.json)
records the full scores.

This is one **development** recording and a forecast of *GPS receiver reports*,
not a calibrated estimate of the aircraft's true position. The IMU error law
came from generated controls; its noise levels and coverage have not been
established for this instrument. The fit parameters are treated as fixed in
the conditional covariance. Seven other ESA flight groups remain reserved.
No Earth-model conclusion follows from this check; the scientific decision
remains **abstain**.

Two preceding technical attempts are retained: the [first reached its work
limit](CONDITIONAL_FORECAST_V1_RESULT.md), and the [second compared unlike
covariance hashes](CONDITIONAL_FORECAST_V2_RESULT.md). The
[corrected frozen plan](CONDITIONAL_FORECAST_V3_PLAN.md) records the successful
single-pass method.
