# Global calibration and rotating-force bound controls

**30/30 identities passed** in 4.51 seconds. The study charged 12,726 software reference/value evaluations, with no original reads or native-engine fits.

| Control | Passed | Maximum actual remainder / bound | Largest repository/reference difference |
|---|---:|---:|---:|
| calibration | 12/12 | 1 | 0 |
| packet | 12/12 | 0.947508 | 5.69e-14 |
| history | 6/6 | 0.894283 | 4.44e-16 |

The bounds come from global analytic inequalities, not the largest sampled error. Probes test their implementation. Fixed-time body preintegration is covered; candidate-specific geographic dynamics, timing across packet boundaries and a whole-record floating-point enclosure remain outside this result. No archive prediction fit is authorized by these controls.

[Proof outline and frozen limits](PLAN.md) · [Prediction interface](../ilvis0-bounded-prediction-controls/NATIVE_INTERFACE.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
