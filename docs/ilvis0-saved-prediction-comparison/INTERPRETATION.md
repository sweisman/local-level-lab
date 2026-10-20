# The advantage persists when later GPS positions are withheld

The saved calculations contain a useful empirical check. Calibration uses the
first 4.85 minutes of one IMU21 recording. The later **IMU (inertial measurement
unit)** readings continue the reconstructed track for another 2.43 minutes;
later GPS positions are withheld from calibration and used to assess its errors.
There is no GPS reset at the split.

Three matched settings have all three source optimizations completed. Their
direct errors are:

| Model | Training horizontal RMS | Later horizontal RMS | Later vertical RMS |
|---|---:|---:|---:|
| Globe + specified field | 0.041–0.042 m | **2.38–2.45 m** | 3.23–3.33 m |
| Globe, zero field | 25.26–29.35 m | 142.91–160.56 m | 1.98–2.03 m |
| Flat disc | 8.69–14.08 m | 165.96–255.36 m | 2.16–3.17 m |

RMS summarizes the typical size of the errors over each period. The advantage
is already present in training and persists after later GPS positions are
withheld. These models did not start the prediction period with equally good
training fits. Vertical error alone does not give the same ordering; both
horizontal and vertical performance matter.

![Direct errors and a closer view of the specified-field globe](prediction-errors.png)

The [complete audit](README.md) includes all **18 saved fits**, under three
fitting/error assumptions and two processing cases. Fifteen passed their original
stopping checks; three remain unfinished. All use **the same recording and the
same receiver split**, not eighteen independent flights. The three incomplete
matched settings remain visible; their missing best fits are not counted as
equal support for the models.

This adds no new fit, model preference or independent replication. It verifies
the saved epoch errors against their original summaries and keeps their stopping
labels unchanged. The recording had already informed development, calibration
uncertainty is not covered by these error curves, and no calibrated absolute
adequacy threshold or detection significance follows from them.

[Source and every comparison](README.md) · [Comparison CSV](comparisons.csv) ·
[Fixed error sections](sections.csv) · [Next analyses](../NEXT_STEPS.md).
