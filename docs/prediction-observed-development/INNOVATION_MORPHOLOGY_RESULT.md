# The saved height error changes slowly

The [saved-only audit](INNOVATION_MORPHOLOGY_PLAN.md) measured the pattern left
in the first 600 receiver reports after each complete ESA development fit.
It verified the archived fits and reproduced the previously published
correlations. No measurement, later receiver report or reserved flight group
was opened, and no model was refitted. Reports are about one second apart.

| Whitened fitted error | One report apart | Five reports apart | Twenty reports apart | Share of mean-removed power at periods over 60 reports |
|---|---:|---:|---:|---:|
| North | 0.190 | 0.113 | −0.022 | 13.5% |
| East | 0.366 | 0.232 | −0.015 | 17.4% |
| **Height** | **0.825** | **0.741** | **0.538** | **71.2%** |

The point-sampled law gives almost identical values. For height, **66.5%**
of the mean-removed power lies at periods over 120 reports. Same-time
cross-axis correlations are −0.197 north/east, +0.183 north/height and
+0.054 east/height. The saved result contains all 120 lag values per axis.

A two-parameter exponential-plus-white curve matched to height lags 1 and 20
has a descriptive scale of **44.6 reports** and predicts correlation 0.754
at lag 5, close to the measured 0.741. It is **not a qualified error law**:
the measured height correlation becomes negative by lag 80, whereas that
simple positive exponential remains positive. Fitting calibration to the same
600 reports also changes these residuals. The [local fit projection check](LOCAL_PROJECTION_NULL_RESULT.md)
shows that white error passed through that projection alone does not produce
the observed persistence.

This pattern is a target for independently generated changing-error and
motion controls. It does not identify whether the source is the gyroscope,
accelerometer, receiver, motion model or calibration. The two complete-fit
generated controls are running separately; the aircraft error law and
forecast uncertainty remain unqualified.

[Saved numeric audit](innovation-morphology-result.json) ·
[Earlier training-error result](TRAINING_INNOVATION_RESULT.md)
