# Saved ESA prediction-error scale check

Question: how do the withheld IMU-based prediction errors compare with the
primary receiver's own reported position precision? This is an **error-budget
diagnostic**, not a model decision or a test of the receiver's true accuracy.

Use only the sealed development release `docs/esa-observed-wide-pilot`:
manifest SHA-256 `73aa91117d60ca191f614f0fe826167e8b237fcff320b7676e2f505fd1bf6289`,
summary SHA-256 `2ce3ae7c4e48adb8d5d3048316a68d88a3015ff1528a3515bb212d1081e15f31`,
and scoring input SHA-256 `5cce2704433e7dece8eec336882692e15194d6c882d8e2bd7efa67265a172c2b`.
Retain all 24 task identities, including the two failed fits. Compare every
available saved error curve with the same epoch's sealed receiver covariance;
verify exact timing and receiver coordinates before calculating ratios.

Report later north/east/up error RMS, median reported standard deviation and
median absolute error divided by that reported deviation for each completed
fit. Keep training and prediction separate. Use the existing `lll.studies`
closed-study hash checks and record this reporter's source hash. There are
**zero** native evaluations, model fits, original-data reads and protected ESA
reads. Do not adjust forecasts, working weights or model rankings.

The 22 available forecasts share one development recording, so neither their
epochs nor their alternate starts are independent replications. Receiver
precision omits accumulated IMU and fitted-calibration error. These ratios
cannot calibrate a prediction threshold or establish significance.
