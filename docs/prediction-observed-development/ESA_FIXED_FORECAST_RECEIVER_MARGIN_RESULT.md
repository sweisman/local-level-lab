# How far would the receiver path have to move to tie these forecasts?

The [fixed-forecast sensitivity check](ESA_FIXED_FORECAST_RECEIVER_MARGIN_PLAN.md)
uses only the sealed ESA development fits and their 120 later receiver reports.
All six original model scores reproduce the saved report before calculating
the margins. Three exact geometry tests pass. The
[complete result](esa-fixed-forecast-receiver-margin-result.json) binds the
source, plan, code and study manifests. No original file, model fit, native
forecast or reserved flight group was used.

For each pair, the table gives the smallest change to the later receiver
positions that would make the **same two saved forecasts** tie in total
sum-of-squares error. “Arbitrary” can change independently at each report;
“constant” is one north/east/up offset applied to every report.

| Competing forecast | Arbitrary shift, per-report RMS | Constant shift | Horizontal-only arbitrary shift |
|---|---:|---:|---:|
| Globe, zero field | 1,296 m | 1,338 m | 1,295 m |
| Flat disc, zero field | 2,000 m | 2,063 m | 2,000 m |

Both complete processing settings give the same margins to the nearest
metre. These numbers are much larger than the centimetre-scale differences
among the three parallel GNSS-only PPP exports on this opened flight. The
current numerical preference therefore does not hinge on *which of those
three exports* supplies the 120 later positions.

The result is deliberately narrow. The forecasts, their calibration, the
receiver coordinate metric and the 120-report development horizon are held
fixed. Refit models, change the coordinate construction, or allow an error
shared by all PPP exports, and the margin can change. A poor competing fit
can also create a large margin without proving the preferred model is
physically adequate. This does not establish an absolute receiver error
bound, independent replication, a calibrated false-choice rate or an
Earth-model decision.
