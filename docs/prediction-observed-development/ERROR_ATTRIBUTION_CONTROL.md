# Can these sampled channels reveal their physical cause?

A deterministic software control constructs two different worlds. In one, an aircraft-like platform has a small pitch and forward vibration (10 Hz, 0.029° pitch and 0.2 mm displacement). In the other, the platform is steady while correlated sensor error reproduces those IMU readings. A constant receiver offset reproduces the same one-second position reports. Both worlds also share independently seeded white noise and changing bias.

All 9,000 IMU samples and 31 receiver reports are **exactly identical** between the worlds. Their true gyro rates differ by up to 0.03142 rad/s. The observed gyro Y / force X short-span correlation is -0.679 in both.

The values were not fitted to the ESA recording. This is an adversarial example, not a claim that its instrument has such coupling. It proves that correlation in these sampled channels alone cannot identify aircraft vibration versus correlated sensor error. Independent motion constraints or an effective prediction-error envelope are needed. No original or reserved aircraft data were opened.

[Control configuration and hashes](ERROR_ATTRIBUTION_CONTROL.json) · [Next qualification](OBSERVED_ERROR_PLAN.md).
