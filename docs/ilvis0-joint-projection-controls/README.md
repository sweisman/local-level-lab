# Joint error covariance for training summaries

The shared operator can now propagate its supplied receiver-plus-IMU error law through fixed averages and trends without forming a whole-record covariance matrix. These are software controls with generated inputs, not aircraft fits or estimates of device noise.

| Control | Epochs | Probe columns | Summary rows | Accounted workspace (MiB) | Time (s) | Result |
|---|---:|---:|---:|---:|---:|---|
| small | 5 | 27 | 12 | 0.03 | 0.01 | Passed |
| long | 64080 | 2 | 12 | 88.01 | 52.07 | Passed |

Small controls compare inverse, transpose and projected covariance against an independent dense reference, including cross-axis and time correlations. The long control checks inverse round-trip stability, transpose duality and linear-memory operation at 64,080 epochs. It does not build that record’s dense covariance.

The twelve summary rows are fixed functions of time. They do not discard physical calibration parameters or estimate a noise law. Correct propagation under the supplied linear law is separate from nonlinear calibration uncertainty, numerical interval certification and observed coverage. **V01 remains unqualified.**

[Frozen checks and limits](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
