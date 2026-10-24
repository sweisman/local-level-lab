# Noisy calibration and later-position prediction

**24/24 raw forecasts meet the physical error limits; 20/24 pass the numerical stopping checks.**

Later horizontal RMS is 1.84–2.08 m; height RMS is 0.17–0.25 m.
All 24/24 earlier-error-conditioned forecasts also meet the physical screen.

The study uses generated two-minute turning and climbing records with known IMU and receiver errors.
Calibration uses 79 earlier positions; 40 later positions are withheld until the forecasts are saved.
Both recorded-increment and endpoint-shared rate-sample error formats are tested.
Each candidate predicts its own generating truth: these are not Earth-model votes.

24/24 completed fits reach at least one calibration boundary.
The unrestricted linear uncertainty calculation cannot certify those boundary cases.
Accurate point forecasts therefore do not establish calibrated confidence.

**The complete prediction/uncertainty gate is not qualified.** All numerical failures and
unsupported calibration cases remain recorded. The original twenty-minute noisy failure
and the 53-stretch findings are unchanged.

[Complete results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md)

| Case | Numerical pass | Later horizontal RMS | Later height RMS | Calibration diagnostic |
|---|---|---:|---:|---|
| increment-sphere_rotating-0-0 | Yes | 2.014 m | 0.168 m | active bounds unsupported |
| increment-sphere_rotating-0-1 | Yes | 2.014 m | 0.168 m | active bounds unsupported |
| increment-sphere_rotating-1-0 | No | 1.836 m | 0.171 m | active bounds unsupported |
| increment-sphere_rotating-1-1 | No | 1.836 m | 0.171 m | active bounds unsupported |
| increment-sphere_still-0-0 | Yes | 2.025 m | 0.167 m | active bounds unsupported |
| increment-sphere_still-0-1 | Yes | 2.025 m | 0.167 m | active bounds unsupported |
| increment-sphere_still-1-0 | Yes | 1.853 m | 0.168 m | active bounds unsupported |
| increment-sphere_still-1-1 | Yes | 1.853 m | 0.168 m | active bounds unsupported |
| increment-flat_still-0-0 | Yes | 2.050 m | 0.187 m | active bounds unsupported |
| increment-flat_still-0-1 | Yes | 2.050 m | 0.187 m | active bounds unsupported |
| increment-flat_still-1-0 | Yes | 1.871 m | 0.185 m | active bounds unsupported |
| increment-flat_still-1-1 | Yes | 1.871 m | 0.185 m | active bounds unsupported |
| point-sphere_rotating-0-0 | Yes | 2.051 m | 0.228 m | active bounds unsupported |
| point-sphere_rotating-0-1 | Yes | 2.051 m | 0.228 m | active bounds unsupported |
| point-sphere_rotating-1-0 | Yes | 1.906 m | 0.230 m | active bounds unsupported |
| point-sphere_rotating-1-1 | Yes | 1.906 m | 0.230 m | active bounds unsupported |
| point-sphere_still-0-0 | Yes | 2.061 m | 0.228 m | active bounds unsupported |
| point-sphere_still-0-1 | Yes | 2.061 m | 0.228 m | active bounds unsupported |
| point-sphere_still-1-0 | No | 1.922 m | 0.228 m | active bounds unsupported |
| point-sphere_still-1-1 | No | 1.922 m | 0.228 m | active bounds unsupported |
| point-flat_still-0-0 | Yes | 2.077 m | 0.252 m | active bounds unsupported |
| point-flat_still-0-1 | Yes | 2.077 m | 0.252 m | active bounds unsupported |
| point-flat_still-1-0 | Yes | 1.922 m | 0.253 m | active bounds unsupported |
| point-flat_still-1-1 | Yes | 1.922 m | 0.253 m | active bounds unsupported |

Wall time: 31.05 minutes. Attempted native calls: 1,429,708; prepaid allowance: 1,438,896.

The error-conditioned physical-position target omits future receiver-error contributions.
No later receiver coordinates choose weights or corrections. Original aircraft and
protected confirmation recordings are not inputs.

[Software qualification](../integrated-noise-covariance/shared-native-protocol-qualification/README.md) ·
[Reproducibility](../REPRODUCIBILITY.md).
