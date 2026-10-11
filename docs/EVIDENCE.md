# Evidence so far

An **IMU (inertial measurement unit)** measures turning and acceleration.
The project's empirical evidence comes primarily from NASA survey-grade airborne IMUs.
Stationary consumer crowdsourcing is a separate developing experiment.

## NASA archive

All 53 selected high-speed stretches have been analyzed. Twelve have complete comparisons
favoring globe over the specified flat disc under both processing assumptions; all twelve
then favor rotating over still globe. None has a complete flat preference. Forty-one
remain unresolved because required numerical fits did not finish. These are model-fit
preferences, without independently calibrated statistical significance.

The [source-aware findings](ilvis0-highspeed-segments-20261008/FINDINGS.md) give durations,
speeds, instrument record types and partial results. The [analysis roadmap](ANALYSIS_ROADMAP.md)
tracks smaller numerical, timing, calibration and prediction checks. Overlapping streams
and repeated flights are not counted as independent instruments.

## Stationary consumer experiment

The Android app now guides still A/B reversals on a solid surface. Its preliminary analyzer
estimates a signed horizontal reversal signal without latitude or an expected rotation
amplitude. No real consumer unit has yet completed the required slow-rate validation here.
Software tests establish specific behavior; they are not detections of a geographic field.

See the [stationary method](STATIONARY.md), [instrument checks](BENCH.md) and
[validation plan](VALIDATION.md). Geographic pooling and calibrated uncertainty remain future work.

## Historical passenger-flight work

Two 1,000-attempt synthetic pilots and later route/turn studies remain recorded in the
[technical evidence](EVIDENCE_TECHNICAL.md) and [technical validation history](VALIDATION_TECHNICAL.md).
They explored aircraft collection and exposed motion, wind and sensor limitations.
They do not validate the new ground protocol. No simulation campaign was rerun for this change.
