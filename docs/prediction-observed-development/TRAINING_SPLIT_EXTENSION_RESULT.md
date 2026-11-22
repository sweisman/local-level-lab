# What happens when the same ESA fit predicts longer

This development check holds the fitted calibration fixed. It uses receiver
reports 0–599 to fit the model, then predicts reports 600–999. Both declared
IMU input-error laws completed. Neither later receiver positions nor the seven
reserved confirmation flights entered the calculation. The extended raw and
conditioned forecasts reproduce the earlier 600/200 forecasts **exactly** on
reports 600–799, and the original training cost and error-law determinant
replay under the longer calculation.

| Later reports | Same 600-report fit: heights inside nominal 95% range | Same fit: conditioned height RMS | Earlier 800-report fit: heights inside range |
|---|---:|---:|---:|
| 600–699 | 100/100 | 0.19 m | — |
| 700–799 | 100/100 | 0.28 m | — |
| 800–899 | 96/100 | 2.25 m | 25/100 |
| 900–999 | **0/100** | **8.47 m** | **0/100** |

The table shows the increment law; the point law gives virtually identical
numbers. The last column uses the older fit to reports 0–799, scored against
**the same receiver positions** for reports 800–999. The two fits differ, but
both forecasts lose nominal height coverage by reports 900–999. Extending the
600-report fit also increases its conditioned horizontal RMS from 1.94 m on
reports 600–799 to 14.25 m over reports 600–999. Its 400-report conditioned
height RMS is 4.39 m, with 296/400 heights inside nominal ranges.

The saved signed height errors average **−0.15, −0.23, +1.90 and +8.13 m** in
the four successive 100-report bins. In the last two bins the receiver's mean
vertical speed is about +0.03 and −0.05 m/s, while the prediction error grows
upward. This is a coherent forecast drift, not just scattered large errors;
it does not identify which motion or instrument assumption causes it.

The matched continuation shows that the earlier 200-report success did not
extend to the next 200 reports. Changing the training endpoint changes *when*
coverage starts to fail, but does not remove the later failure. It does not
identify the physical cause. The height errors persist strongly from one
report to the next: the saved marginal-error check gives lag-one correlation
about **0.99995** for the 600/400 forecast. Its 104 missed height ranges are
therefore a sustained drift, not 104 independent events. This check uses each
report's stated interval; it is not a whitening test of the full covariance.
The nominal ranges come from an assumed error law and are not calibrated
95% confidence ranges for aircraft data. This is
one retrospective development recording and one tested physical model; it
cannot decide Earth geometry or establish independent predictive validity.
The scientific decision remains **abstain**.

The [predeclared extension](TRAINING_SPLIT_EXTENSION_PLAN.md) records the
finite work limits and no-leak rule. The [saved comparison](training-split-extension-score.json)
records the 100-report bins, both error laws, source hashes, numerical fit
history and the exact shared interval. The sealed study completed 2/2 tasks,
with 0 errors and no active locks. The next gate is an observed error law that
predicts this changing height error from training-only evidence before any
reserved flight is used.
