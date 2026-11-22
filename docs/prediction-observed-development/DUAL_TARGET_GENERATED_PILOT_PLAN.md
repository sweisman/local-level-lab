# Finite dual-target generated forecast pilot

## Question

Can one complete training-only generated fit seal **both** physical-position
and receiver-measurement predictive bounds before later truth is available?
This is a technical pilot for the [noise-aware qualification](NOISE_AWARE_ADEQUACY_PLAN.md),
not an aircraft coverage test or a new Earth-model campaign.

## Frozen cases and limits

- Use the existing 300 Hz, 900-second rotating-globe generated route at 55° N,
  600 earlier and 300 later reports, the unchanged 26 nuisance columns,
  bounds, clock, starting point, receiver policy and 200-evaluation ceiling.
- Use fresh seeds **650101** for increment noise and **650102** for point noise.
  A separate 10-second, nine-report preflight uses increment seed **650000**
  with eight fit evaluations. None reuses a completed study's task identity.
- The shared base allowance covers one full forecast error-operator pass.
  The ordinary and bounded diagnostics each build an operator for each target,
  for four passes total. Prepay **three additional** complete passes per task,
  each with `n + q`
  native calls and packet visits (`n` IMU intervals and `q` receiver queries).
  Use two one-thread workers and a six-hour full-run ceiling. Do not expand
  an active allowance after a failure.
- Require source-bound software checks, a separate recovery qualification,
  and a passing preflight. Persist hashed outputs and task charges through
  the shared `lll.studies` lifecycle. An interrupted task may resume only
  under its qualified, separately charged recovery rule.

## Technical gate

Both bounds and both diagnostic records must exist, share the same fitted
point and declared error law, retain all 26 calibration columns, use only
earlier receiver observations and have the correct distinct prediction
targets. The ordinary physical forecast and original known-truth scores stay
unchanged. Later generated truth is opened only after both bounds are saved.
Report numerical convergence and the inherited physical path screen
separately. The [noise-floor finding](GENERATED_NOISE_FLOOR_AUDIT_RESULT.md)
does not permit relabeling that screen.

This pilot does **not** yet generate later noisy receiver measurements, so
receiver-target empirical coverage is outside its claim. A later fresh study
must score both targets, varied routes, calibration effects and held-out
coverage. No original or reserved aircraft data may be read. Scientific
decision: **abstain**.
