# Solver qualification on known controls

**34/34 bounded software starts passed their predefined checks.** They used 826 actual evaluations, with no start exceeding 200. No NASA original was opened and no observed Earth-model fit was started. The frozen solver was not changed.

An **IMU (inertial measurement unit)** records turning and acceleration. This matrix checks whether the solver recovers known answers, including deliberately weak calibration directions, and short analytic IMU/GPS trajectories.

## Results

| Control | Starts passed | Largest actual evaluation count | Largest prediction error |
|---|---:|---:|---:|
| interior | 3/3 | 14 | 2.7e-09 normalized residual |
| boundary | 3/3 | 10 | 1.11e-16 normalized residual |
| redundant | 3/3 | 9 | 8.44e-15 normalized residual |
| scaled | 3/3 | 11 | 2.58e-11 normalized residual |
| nonlinear | 3/3 | 10 | 2.71e-12 normalized residual |
| gain offset | 3/3 | 19 | 1.72e-09 normalized residual |
| bias | 2/2 | 56 | 1.41e-09 m |
| effective orientation | 2/2 | 68 | 2.12e-08 m |
| gain | 2/2 | 53 | 2.96e-06 m |
| timing | 2/2 | 53 | 1.44e-06 m |
| stationary rotating | 2/2 | 29 | 0 m |
| stationary still | 2/2 | 29 | 0 m |
| east rotating | 2/2 | 29 | 0 m |
| east still | 2/2 | 29 | 0 m |

The six analytic problems use exact functions and derivatives. Their known feasible optima include an interior solution, a constrained boundary, redundant parameters, a badly scaled weak direction, nonlinear curvature, and coupled gyro gain/offset. Three starts per problem include zero and two fixed-seed starting points. Nonunique or numerically weak coordinates must recover predictions and objective values; unique parameter recovery is not required for them.

The eight IMU/GPS fixtures use two-second analytic trajectories and two starts each. Four test offset, effective orientation, gain and timing. Four test stationary and constant-speed equatorial eastward globe motion, with or without a background rotation term. Their GPS positions and angle/velocity increments are generated directly from closed-form trajectories, rather than by asking the prediction kernel to generate its own observations. No fused navigation quantities or real-flight residuals enter them.

For these motion controls, tangent derivatives are independently computed from the native value kernel using second-order finite differences. Every underlying prediction, including truth and final checks, counts toward the 200-per-start limit. This differs from the archive’s automatic-differentiation tangent backend; it is a check of the frozen optimizer and value predictions, not full qualification of that backend.

## Interpretation and remaining checks

These results show that the solver can finish the predefined small problems, distinguish poor constrained optima from numerical failure, and recover identifiable corrections under known kinematics. The stationary/eastward controls exercise background and transport rotation separately. Known calibration errors are recovered within the limits specified before running the matrix.

They do not establish that the 26/27-parameter, minutes-long NASA fits will finish or have a global optimum. The generators share the declared coordinate and inertial conventions; they do not independently prove those conventions describe real flights. These noiseless software controls do not qualify a survey instrument, calibrate uncertainty, or justify relabeling any unfinished archive result. The matched observed solver trial still finished 10/12 fits versus 11/12 originally.

The next bounded observed comparison tests the integration clock on the already completed control stretch, with unchanged calibration assumptions and the original frozen optimizer. Its finite allowance requires approval before starting. See the [analysis roadmap](../ANALYSIS_ROADMAP.md).

## Evidence and reproduction

[Per-start ledger](controls.csv) preserves numerical status, objective agreement, errors, boundaries and failures. Source and environment hashes, native-build provenance and the complete result records accompany this report. The run is complete and frozen; do not rerun its numerical starts. Packaging and reporting perform no fits:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-solver-qualification-20261010/run_controls.py --package-only
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-solver-qualification-20261010/build_report.py
```
