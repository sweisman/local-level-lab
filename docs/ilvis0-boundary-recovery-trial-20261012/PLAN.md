# Boundary-aware continuation: finite trial

Use the same three preselected unfinished stretches and completed control as the
two earlier recovery trials. Start from the original saved first-pass points,
preserving every earlier result and using a separate source/input/environment freeze.

- 15 unfinished primary fits, six completed control fits and three prescribed repeats.
- At most 600 residual/tangent calls and two value predictions per start:
  **24 starts / 14,448 native sweeps**, no retries or replacement starts.
- The boundary-aware solver takes bounded linear least-squares steps and verifies
  actual nonlinear costs, shortening rejected steps. Snap only normalized boundary
  slack of at most `1e-12`; record the initial change.
- Keep stationarity `1e-4`, relative cost stability `1e-8` and relative residual
  stability `1e-6`. Every passing fit needs the existing fresh bounded-stability check.
- Preserve physical models, calibration bounds, nominal 200 Hz timing,
  `h1_v3_tau60` covariance, ±1°/hour offsets and both processing assumptions.
- Use the original fixed 0.01 perturbations. Reuse completed reference fits where
  the original selection specifies; never choose a better starting point after
  inspecting the newer trial costs.
- All 24 planned starts must pass. Controls and repeats must also agree in relative
  cost within `1e-6` and in every-axis predicted position within 0.01 m RMS.
- Retain per-evaluation costs, accepted/rejected step fractions, final residuals and
  Jacobians, epoch errors, source hashes and charged append-only journals.
- One durable worker with two BLAS threads. Charge calls before execution.
  Interrupted identities stay spent and unresolved; completed trials cannot resume.
- Estimated runtime at the ceiling: **10–14 hours**, based on the same recordings'
  prior evaluation times. Warm starts may finish sooner; the extra bounded linear
  calculations are not yet timed on the full observation model.

The [software comparison](../ilvis0-boundary-controls-20261012/README.md) passed
40/40 known-answer controls with this candidate, versus 35/40 for the original
rectangular method and 38/40 with an exactly snapped start. Software success alone
does not resolve recordings. This trial tests transfer to the actual observation
model. It issues no calibrated scientific decisions and does not change the
original 12 globe preferences, zero completed flat preferences and 41 unresolved.

Success supports the separately frozen all-41 recovery stage. Failure remains
recorded and cannot be erased by spending unused allowance on retries.
