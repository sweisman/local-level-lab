# What can identical recorded inputs predict?

This local planar software control gives two paths exactly the same 800 seconds of earlier receiver positions and the same recorded IMU stream throughout. After receiver positions are withheld, one path turns gently and its IMU is ideal. The other continues straight while a new gyro error and matching lateral-force error produce the same recorded IMU readings. At 80 m/s and an illustrative 1°/hour rate, their positions separate by 2.79 m after 120 seconds.

The new errors start exactly when positions are withheld. This is an adversarial possibility, **not** an estimate of either archived IMU, a likely aircraft event or a calibrated error limit. It shows why a short forecast still needs independently justified limits on changing sensor error and unmodeled aircraft motion. No aircraft data or physical-model fit entered this calculation.

[Configuration and source hash](FORECAST_AMBIGUITY_CONTROL.json) · [Observed error qualification](OBSERVED_ERROR_PLAN.md).
