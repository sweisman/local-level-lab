# Training narrows two parameter intervals

All six saved-data checks pass. The tested coordinate bounds narrow only the initial vertical-position offset and clock offset. Individual orientation, gyro calibration and accelerometer calibration intervals retain their original limits.

The table gives each remaining interval width as a percentage of its original width.

| Candidate | Processing | Vertical offset | Clock offset |
|---|---|---:|---:|
| Specified-field globe | Zero removal | 34.3% | 88.0% |
| Specified-field globe | Profiled removal | 34.7% | 88.0% |
| Zero-field globe | Zero removal | 33.0% | 86.8% |
| Zero-field globe | Profiled removal | 33.1% | 86.8% |
| Flat disc | Zero removal | 30.0% | 87.0% |
| Flat disc | Profiled removal | 30.6% | 87.3% |

This projection gives no narrower individual sensor-calibration intervals. That does not mean the training data contain no calibration information: coupled relationships between parameters remain important. Nor does it prove every point in the coordinate box is feasible.

The attitude and accelerometer-gain inputs to the saved mounting-transform bound are unchanged. Repeating that transform calculation with these coordinate bounds would leave its allowance unchanged. A stronger method must preserve useful relationships between parameters or qualify smaller regions that together cover the full domain.

The audit used 324 proposals and 972 exact support checks, with all 51 coordinates and all 30 training inequalities retained. Execution took 14.41 seconds on one thread. Accounting journals reconcile with the frozen limits. No aircraft reads, integration, new trajectory bounds or model fits ran. V01 remains unqualified.

[All 162 parameter intervals](parameter-intervals.csv) · [Scope](PLAN.md) · [Preserved first-wrapper failures](../ilvis0-calibration-box-audit/README.md) · [Original allowance audit](../ilvis0-proof-budget-audit/README.md) · [Next diagnostic](NEXT_PLAN.md) · [Reproduce](../REPRODUCIBILITY.md).
