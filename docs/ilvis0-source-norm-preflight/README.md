# Source-level norm preflight

6/6 source controls passed.

| Candidate / removal | Passed | Original vertical width (m/s²) | Geometric width (m/s²) | Combined width (m/s²) | Fraction retained |
|---|---|---:|---:|---:|---:|
| Globe with specified field / zero | Yes | 0.01142092 | 0.0007101336 | 0.0007101336 | 0.062178 |
| Globe with specified field / profiled | Yes | 0.01142092 | 0.0007172999 | 0.0007172999 | 0.062806 |
| Globe with zero field / zero | Yes | 0.01142092 | 0.0006624068 | 0.0006624068 | 0.057999 |
| Globe with zero field / profiled | Yes | 0.01142092 | 0.0006767449 | 0.0006767449 | 0.059255 |
| Flat disc / zero | Yes | 0.01142092 | 0.0006379411 | 0.0006379411 | 0.055857 |
| Flat disc / profiled | Yes | 0.01142092 | 0.0006557276 | 0.0006557276 | 0.057415 |

Elapsed 3.45 seconds. Reserved 9600/9,600 bounded-prefix visits and 9600/9,600 point-oracle visits, plus 84/84 scalar checks.

The baseline uses the same saved source, body prefix and training-conditioned force range. The literal installation-matrix metric defect is bounded explicitly. All ranges are fixed before the known calibration is read. No original aircraft data or protected ESA data is used.

This is a value-only component diagnostic. It does not qualify a Taylor remainder, native reference coefficients, a full position prediction or observational coverage. No full native integration, propagation bound, LP or fit ran.

[Frozen scope](PLAN.md) · [Operator derivation](../ilvis0-directional-dynamics/OPERATOR_DERIVATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
