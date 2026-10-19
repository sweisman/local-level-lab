# Matched horizontal-only multi-start comparison

## Purpose and unchanged observations

The first two-recording sensitivity study leaves IMU21 unresolved at its repeat
gate. Fixed-point diagnosis finds coupled timing/calibration solutions, with
no gross timing-derivative fault. The separate known-answer multi-start controls
must pass before this study can launch. This is not a new corpus selection.

Use the exact preselected 4.07-minute IMU21 recording and original measurements.
Retain both IMU channels, nominal 200 Hz integration, the existing horizontal
covariance, all nuisance columns, ±1°/hour offset bounds, both processing cases,
and unchanged fresh stationarity/cost/position stopping limits. The earlier
IMU8 comparison and 53-stretch full-position findings remain preserved.

## Starts and selection

Give every model and processing case the same three normalized timing starts:
**−0.8, 0, +0.8**, corresponding to −120, 0 and +120 ms. Use two independent
non-timing seed families: the original full-position fit, and the original
receiver/IMU initialization used by the first study. Do not copy the new primary
solution into its repeat. The grid is identical to the qualified software grid.

This gives 3 models ×2 cases ×2 seed families ×3 timing starts = **36 target
starts**. Add **two fresh IMU8 specified-field/unsubtracted controls**, initialized
at the earlier matched horizontal primary and repeat endpoints. Eight separately
charged projected residual/Jacobian checks must reproduce the parent arrays
exactly before fitting. Controls must reproduce the earlier score/predictions
and pass their own repeat gate.

Each family selects its lowest returned unmodified cost, with deterministic
identity tie-breaking. Preserve every start and failure. A lower-cost unfinished
fit cannot be ignored in favor of a higher-cost converged result; a missing or
invalid outcome makes that group unresolved. Selected solutions must separately
pass the original numerical gate and the unchanged 1e−8 relative cost /1 mm
axis-RMS /1 cm epoch-maximum repeat checks. Only complete case/model comparisons
enter the shape-first hierarchy. This search is not a global-optimum proof.

## Finite allowance and runtime

- **38 optimizer starts**, at most **200 tangent calls per start**.
- **One full prediction diagnostic per start**, plus **eight preflight calls**.
- **7,646 native calls maximum**, four total numerical threads.
- **20-hour wall ceiling**, no retries, continuation or expansion.

The preceding IMU21 fits took about 1.93 hours for twelve starts. Tripling those
starts suggests roughly **six hours**, but convergence paths may differ. At the
measured slowest IMU21 call rate, the full allowance is about 18.5 hours. The
longer IMU8 controls are warm-started; the wall ceiling applies regardless.

Freeze sources, inputs, environment, original containers, start vectors and
qualification receipts before launch. Use exclusive locks and append-only
pre-call charges; save atomic hashed fit, tangent and full-prediction artifacts.
An interrupted start stays charged and cannot restart. Completion closes unused
allowance. Publication uses saved artifacts only and runs automatically.

## Limits of interpretation

Large unscored height errors and flat vertical null directions remain visible.
Even a completed horizontal comparison is not adequate full-flight reconstruction,
gyro-only evidence, coordinate independence or calibrated significance. Existing
shape and retained-background-field names do not identify the field's cause.
