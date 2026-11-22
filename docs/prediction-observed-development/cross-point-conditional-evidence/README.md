# Two saved ESA fits under one conditional error law

This retrospective development check compared two previously saved calibration
settings on one 20-minute ESA recording. Each forecast used the first 800 GPS
reports and the recorded IMU stream. The next 400 GPS reports were opened only
after both forecasts were sealed. The same declared IMU and receiver error law
was applied to both settings, with no new fitting.

| Saved calibration setting | Uncorrected horizontal RMS | Conditional horizontal RMS | Conditional vertical RMS | Preset physical screen |
|---|---:|---:|---:|---|
| Receiver-only fit | 7.8 m | 9.07 m | 12.86 m | Passes |
| IMU-error-weighted fit | 249.4 m | **2.85 m** | 11.88 m | Passes |

The large uncorrected miss at the weighted setting was corrected by the
training-period error estimate under this declared law. That setting predicted
the later receiver reports more closely after conditioning. The receiver-only
setting's small uncorrected miss did not produce the better conditional
forecast. This comparison shows why the same prediction rule must be applied
to both saved fits before judging them.

The [machine report](cross-point-conditional-result.json) contains the full
scores and fixed screen. The [frozen plan](CROSS_POINT_CONDITIONAL_PLAN.md)
defines the comparison. The [sealed study](cross-point-conditional-evidence/README.md)
preserves inputs, source, environment, charges and results. Two earlier
technical attempts failed before scoring; their outcomes and work charges
remain preserved. The third attempt passed its 17 source-bound software and
recovery checks, completed its one task in 305 seconds, and charged its
predeclared 450,000 native-call allowance.

These are predictions of GPS receiver reports on **one opened development
recording**. The error law's uncertainty and coverage have not been calibrated
for this instrument. Its 400 later reports are correlated observations from
one flight, not independent replications. Seven reserved ESA flight groups
remain closed. The scientific decision is **abstain**.
