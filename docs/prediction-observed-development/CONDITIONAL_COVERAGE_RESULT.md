# The ESA forecast's uncertainty does not match its vertical errors

The earlier-conditioned forecast passed its preset **position accuracy**
screen on development recording 187. A separate saved-data check now asks
whether its declared uncertainty matches the 400 later GPS receiver reports.
It does not.

| Later receiver component | Inside nominal 95% interval | Normalized error RMS | Predicted standard deviation, first to largest |
|---|---:|---:|---:|
| North | 400/400 | 0.052 | 0.060–52.404 m |
| East | 400/400 | 0.091 | 0.055–50.868 m |
| Up | **25/400** | **6.275** | 0.151–3.556 m |
| All three together | **37/400** inside the nominal 95% ellipsoid | — | — |

The horizontal uncertainty grows very wide compared with the small
horizontal errors. The later vertical receiver-minus-forecast error starts
at −0.07 m and ends at −25.46 m, with a −9.17 m mean. Its declared
uncertainty does not cover this growing difference. Adjacent normalized errors are strongly
correlated, especially in height. The 400 rows are one flight segment, not
400 independent replications; these counts must not be used as a binomial
confidence calculation.

The same weighted fit's uncorrected training-height RMS was 1.40 m. The
later conditional-height RMS is 11.88 m. The mismatch thus grows after the
training split; this comparison alone does not identify its physical cause.

A saved-only decomposition shows the direction of the problem. At the first
later report, the uncorrected path is 4.20 m below GPS and the error law adds
4.28 m upward, nearly cancelling it. By the last report, the uncorrected path
is 9.87 m **above** GPS, but the law still adds 15.59 m upward. That leaves a
25.46 m height miss. Across the 400 reports, the upward conditional correction
averages 9.35 m. This identifies the wrong-way *later correction* in this
recording; it does not establish why the model predicted it.

In the saved training section, GPS-minus-uncorrected-forecast height error
had risen to +4.19 m by the split. Its final 200 receiver reports have a
descriptive linear slope of about +0.98 m/min. The error law carried that
upward correction forward. The actual uncorrected error subsequently changed
direction and ended at −9.87 m. These slopes were examined after seeing the
later result; they diagnose this recording and are not a frozen prediction
rule.

The separate GPS receiver shows no abrupt motion change at that one-second
split: ground speed is 92.175 m/s just before and 92.199 m/s just after;
course changes by 0.010°. Over the surrounding 200-report windows, mean
speed rises from 88.58 to 92.93 m/s and vertical-speed variation falls.
This does not rule out a gradual motion or sensor-error change during the
later section. The [machine diagnostic](conditional-coverage-diagnostic.json)
records the receiver-only boundary values and their source hash.

This check uses the sealed forecast and original later receiver reports. It
does not refit a model or change any declared noise level. All 400 saved
covariance matrices are positive definite. The [machine diagnostic](conditional-coverage-diagnostic.json)
records the exact quantities and source hashes. The [fixed plan](CONDITIONAL_COVERAGE_PLAN.md)
defines the calculation.

The covariance omits uncertainty in the earlier fitted calibration parameters
and its error law came from generated controls. This result does not establish
which omission or physical error causes the vertical mismatch. It **blocks a
calibrated uncertainty claim** for this method. The seven reserved ESA flight
groups remain unopened, and the scientific decision remains **abstain**.
