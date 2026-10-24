# Prediction with known measurement errors

**24/24 forecasts returned; 24 passed numerical checks; 0 meet physical accuracy.**

These are generated controls with receiver and IMU noise, including slowly changing bias.
Their declared noise levels are not measured instrument specifications. There are no observed aircraft inputs.
Each candidate is tested against its own generating truth; these are not votes for a physical model.

| Generating candidate | Removal | Receiver errors | Start | Numerical pass | Physical pass | Later horizontal RMS | Later height RMS |
|---|---|---|---:|---|---|---:|---:|
| sphere_rotating | Zero | reported-short-v1 | 0 | True | False | 84.9438 m | 5.91709 m |
| sphere_rotating | Zero | reported-short-v1 | 1 | True | False | 84.9438 m | 5.91709 m |
| sphere_rotating | Zero | reported-persistent-v1 | 0 | True | False | 84.8339 m | 10.8806 m |
| sphere_rotating | Zero | reported-persistent-v1 | 1 | True | False | 84.8339 m | 10.8806 m |
| sphere_rotating | Profiled | reported-short-v1 | 0 | True | False | 85.3145 m | 5.88735 m |
| sphere_rotating | Profiled | reported-short-v1 | 1 | True | False | 85.3145 m | 5.88735 m |
| sphere_rotating | Profiled | reported-persistent-v1 | 0 | True | False | 86.4109 m | 11.1578 m |
| sphere_rotating | Profiled | reported-persistent-v1 | 1 | True | False | 86.4109 m | 11.1578 m |
| sphere_still | Zero | reported-short-v1 | 0 | True | False | 87.3172 m | 5.86191 m |
| sphere_still | Zero | reported-short-v1 | 1 | True | False | 87.3172 m | 5.86191 m |
| sphere_still | Zero | reported-persistent-v1 | 0 | True | False | 88.5889 m | 11.1522 m |
| sphere_still | Zero | reported-persistent-v1 | 1 | True | False | 88.5889 m | 11.1522 m |
| sphere_still | Profiled | reported-short-v1 | 0 | True | False | 84.8056 m | 5.69478 m |
| sphere_still | Profiled | reported-short-v1 | 1 | True | False | 84.8056 m | 5.69478 m |
| sphere_still | Profiled | reported-persistent-v1 | 0 | True | False | 87.0177 m | 11.0493 m |
| sphere_still | Profiled | reported-persistent-v1 | 1 | True | False | 87.0177 m | 11.0493 m |
| flat_still | Zero | reported-short-v1 | 0 | True | False | 86.4251 m | 5.65462 m |
| flat_still | Zero | reported-short-v1 | 1 | True | False | 86.4251 m | 5.65462 m |
| flat_still | Zero | reported-persistent-v1 | 0 | True | False | 88.4651 m | 11.111 m |
| flat_still | Zero | reported-persistent-v1 | 1 | True | False | 88.4651 m | 11.111 m |
| flat_still | Profiled | reported-short-v1 | 0 | True | False | 83.5545 m | 5.49213 m |
| flat_still | Profiled | reported-short-v1 | 1 | True | False | 83.5545 m | 5.49213 m |
| flat_still | Profiled | reported-persistent-v1 | 0 | True | False | 86.6501 m | 11.0083 m |
| flat_still | Profiled | reported-persistent-v1 | 1 | True | False | 86.6501 m | 11.0083 m |

Elapsed time: 315.35 minutes; charged native calls: 682.

Errors are applied before initialization. Calibration uses noisy earlier positions only; later truth is opened
after the continuous IMU forecast is saved. Accuracy uses the existing observed-prediction limits, including height.
The earlier noiseless software accuracy targets and results remain unchanged.

This is a robustness check under explicit assumptions, not calibrated confidence or an estimate of archive noise.
The receiver-only fitting weights remain fixed; this does not validate them as a complete IMU prediction-error law.
All failures and charges remain preserved. Seven confirmation groups and the 53-stretch findings are unchanged.

[Frozen plan](PLAN.md) · [Earlier error diagnostic](../esa-error-structure/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
