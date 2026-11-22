# Height uncertainty fails at both saved ESA settings

The [same-law forecast comparison](CROSS_POINT_CONDITIONAL_RESULT.md) found
that both saved calibration settings passed the preset **position accuracy**
screen on one opened ESA development flight. This saved-data check asks a
different question: did their declared uncertainty cover the later GPS
receiver reports? The same 400 reports and the same conditional error law
were used for both settings. No fit or forecast was repeated.

| Saved setting | North inside nominal 95% interval | East | Height | Three-axis nominal 95% region | Normalized height-error RMS |
|---|---:|---:|---:|---:|---:|
| Receiver-only fit | 400/400 | 400/400 | **23/400** | 34/400 | 6.69 |
| IMU-error-weighted fit | 400/400 | 400/400 | **25/400** | 37/400 | 6.27 |

Both settings have the same declared height standard-deviation range,
0.15–3.56 m. Their normalized height errors change smoothly through the
later section; adjacent values have correlation above 0.9999. The 400 reports
are one correlated flight sequence, so these counts are descriptive and do
not supply 400 independent trials.

Changing between the two saved parameter settings does not cure the height
coverage failure. The cause is still open: the declared error process may
miss changing motion or instrument error, and the fixed-parameter covariance
omits calibration uncertainty. This result does not determine which cause is
responsible or provide a calibrated replacement law.

The [machine report](cross-point-coverage-result.json) records the scores,
source hash and input identities. The [fixed plan](CROSS_POINT_COVERAGE_PLAN.md)
defines the saved-data calculation. Six focused checks passed. Seven ESA
confirmation flight groups remain closed; the scientific decision is
**abstain**.

A [saved height-error follow-up](CROSS_POINT_HEIGHT_ANATOMY.md) finds 375–377
consecutive range misses after the first 23–25 later reports. The two height
error histories move almost together despite their different calibration
settings. This narrows the next error-law test but does not calibrate a new
range.
