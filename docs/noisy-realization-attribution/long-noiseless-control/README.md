# Full-length clean IMU control

One source-bound software check propagated the **noise-free** rotating-globe
stream through the same twenty-minute, 300 Hz known-correction predictor used
by the noisy oracle. It used 360,000 IMU intervals, 1,200 receiver queries and
one native call. The local test passed; the result, test report and source
binding are hashed in the evidence receipt.

| Error against generating truth | Result |
|---|---:|
| Later horizontal RMS | 0.048 m |
| Later height RMS | 0.060 m |
| Horizontal error at the training boundary | 0.031 m |
| Horizontal error at the final query | 0.064 m |

The existing physical screens are 10 m horizontal RMS and 30 m height RMS.
Thus the long ideal propagation is accurate for this preselected case. It does
not explain why the matched noisy streams missed by 439–508 m with generating
calibration supplied. The published covariance benchmark uses earlier receiver
observations, while the noisy oracle does not. Compare those conditioning
choices first; then use the **same realized noise** to separate gyro,
accelerometer and changing-bias contributions. One clean case does not
qualify all six noisy cases or establish aircraft uncertainty.

[Frozen check](PLAN.md) · [Result](result.json) ·
[Evidence receipt](evidence-receipt.json) ·
[Noise interpretation](../INTERPRETATION.md).
