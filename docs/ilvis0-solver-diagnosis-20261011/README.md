# Why the final flat-disc fit is still unfinished

**The fixed-scale solver reached a nearly stationary flat-disc fit, but did not complete
its required stopping procedure.** All five previously completed fits stayed completed
with closely matched objectives. The sixth remains unfinished; this audit changes no labels.

An **IMU (inertial measurement unit)** records turning and acceleration. This audit reads
the saved results from the same IMU-type-21 recording used in the prediction trial:
2015-10-05, 7.30 minutes, median ground speed 878.1 km/h. No original measurements are
reprocessed. It performs **zero optimizer starts and zero native predictions**.

## What improved and what did not

The unfinished flat-disc fit's stationarity ratio fell from
**39.59** times the permitted threshold to
**9.35e-06**. Its fresh scaled projected gradient was about
9.35 × 10⁻¹⁰, below the unchanged 10⁻⁴ threshold. The training cost changed from
1352.610900 to 1352.283361, a
0.0242% decrease. A small gradient describes
local first-order stationarity within the permitted box; it does not prove a global optimum,
unique calibration, adequate observations or statistical significance.

SciPy did not report successful termination before the 200-evaluation allowance ended.
The last recorded callback was at evaluation 191; its cost
matches the fresh final point. It met the measurement-step and cost-change stability
thresholds, but only **one** consecutive recorded callback met both. The earlier step
changed the residual vector by about 6.15 × 10⁻⁵, above the 10⁻⁶ stability threshold.
Three consecutive stable callbacks were not recorded. The intervening evaluation count
does not establish additional accepted steps or stability.

The replay below uses the already published three-step diagnostic thresholds. It is a
historical diagnostic, not evidence that a different stopping rule would have terminated
these fits at these exact points.

| Processing case | Model | Saved status | Stationarity / threshold: old → new | First three stable callbacks: evaluation | Stable callbacks at end |
|---|---|---|---:|---:|---:|
| bias1_unsubtracted | sphere_rotating | converged | 0.00497 → 0.00548 | 95 | 4 |
| bias1_unsubtracted | sphere_still | converged | 0.00124 → 0.00133 | none | 1 |
| bias1_unsubtracted | flat_still | converged | 8.7e-07 → 9.84e-07 | 141 | 5 |
| bias1_profiled_removal | sphere_rotating | converged | 0.0103 → 0.063 | none | 1 |
| bias1_profiled_removal | sphere_still | converged | 0.000533 → 0.000577 | 96 | 3 |
| bias1_profiled_removal | flat_still | unresolved | 39.6 → 9.35e-06 | none | 1 |

Some successful SciPy stops have fewer than three stable callbacks. Their original
convergence criterion was SciPy success plus the fresh stationarity check; the replay
neither invalidates those saved results nor promotes the unfinished one.

## Calibration and weak directions

| Calibration parameter | New fits at a permitted limit |
|---|---:|
| gyro_bias_z | 6/6 |
| gyro_gain_z | 6/6 |
| gravity_delta | 6/6 |

The unfinished fit has 15 parameters at limits. Its full
Jacobian condition ratio is about 5.15e+07 in normalized
parameter coordinates. Its weakest direction mixes gravity_delta (0.901), gyro_gain_y (0.236), gyro_gain_x (0.224), gyro_gain_z (0.184), accel_bias_z (0.180). These are absolute
loadings; the overall sign of a singular vector is arbitrary. The full direction is
blocked by box limits in both signs.
Full-Jacobian conditioning therefore cannot be read as feasible parameter uncertainty.
Repeated limit saturation still requires a calibration/observation adequacy explanation.
Numerical completion alone cannot settle it.

[Fit diagnostics](fit-diagnostics.csv), [signed parameter changes](parameter-diagnostics.csv),
[three weakest directions per fit](weak-directions.csv) and
[complete recorded callback histories](callback-history.csv) preserve the details.
The [original prediction audit](../ilvis0-prediction-audit-20261011/README.md) documents
the Z gain reversal between whole-stretch and training-only fitting.

## Next numerical test

The evidence supports testing termination based on scaled stationarity **with an
independent stability verification**, rather than treating SciPy's unscaled stopping
flag as the only successful exit. It does not justify gradient-only acceptance, an
automatic budget extension, looser physical bounds or relabeling completed studies.
See [the proposed stopping-rule test](STOPPING_PLAN.md). Qualify that implementation on
known-optimum and false-stop controls before requesting a separate bounded airborne trial.
Do not advance the current fixed-scale candidate to recording replication.

The completed no-removal prediction comparison favors globe. The full comparison
remains unresolved because the removal-allowed flat-disc fit is unfinished. That failure
is not equal support for flat and globe. Rotation remains withheld by the existing hierarchy.

To reproduce this report from saved evidence:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-solver-diagnosis-20261011/build_report.py
```
