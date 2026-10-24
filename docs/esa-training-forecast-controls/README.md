# Learning calibration and predicting later positions

**24/24 generated fits passed every frozen check.** The declared training/forecast calculation qualified.

Each fit starts from earlier receiver positions and raw generated IMU
channels. It estimates calibration with every declared nuisance parameter
active, then predicts the later path without a receiver reset. Later
positions are exposed only after the forecast is saved. True attitude,
velocity, gravity and calibration are not supplied to the fit.

These are two-minute generated maneuvering trajectories, not ESA recordings.
They include the declared sensor biases and gains, with no random measurement
noise added. Their small prediction errors are software results, not measured
instrument accuracy.
Every fit uses its generating geometry; this checks estimation and prediction,
not a calibrated three-model decision.

| Generating geometry | Passed | Converged | Largest later horizontal RMS | Largest later height RMS | Largest later spatial error |
|---|---:|---:|---:|---:|---:|
| Globe with specified field | 8/8 | 8/8 | 1.5185e-05 m | 3.23963e-07 m | 3.62156e-05 m |
| Globe with zero field | 8/8 | 8/8 | 1.49914e-05 m | 3.73718e-07 m | 3.57342e-05 m |
| Tested disc | 8/8 | 8/8 | 4.73236e-05 m | 5.30095e-07 m | 0.00011114 m |

A pass requires the numerical stopping checks, all calibration columns,
horizontal and height RMS at most 0.1 m in both sections, and maximum
spatial error at most 0.5 m. Small errors cannot relabel an unfinished fit.
Neither convergence nor prediction agreement establishes unique calibration.
All starts and failures remain in the evidence.

The run used 1477 native calls in 25.17 minutes.
Saved-only verification checks raw array and prefix hashes, identical inputs
across starts, fit labels, actual work and construction journals. It recomputes
physical errors from saved predictions and independent Cartesian answers,
with the frozen geometry constants. It performs no fit or propagation.

Actual sampling, receiver-error assessment and selection remain open before
observed ESA comparisons. No reserved flight was used and no statistical
confidence or Earth-model detection is claimed.

[Frozen question and allowance](PLAN.md) · [Known-correction controls](../esa-observation-controls/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
