# Frozen scope of the recovery qualification trial

Use the three failure examples and completed control selected in the existing
recovery preparation. Do not select intervals or repeats using model costs or
desired shape preferences. First reproduce each original objective at its saved
point; reconstruct its original initialization, physical bounds and observation
covariance. Reuse already converged reference fits in unresolved stretches.

- Numerical method: `ilvis0-warm-continuation-v1`, bounded dense trust-region
  least squares with Jacobian column scaling, no cold initialization stage.
- Fitting starts: 15 unfinished fits, six completed control fits, three repeats.
- Each start: at most 600 tangent sweeps, including fresh final/stability checks,
  followed by at most two value predictions. Total: 24 starts / 14,448 sweeps.
- Final stationarity: projected relative gradient at most `1e-4`.
- Stability: relative cost change at most `1e-8`, relative residual change at most
  `1e-6`; three stable accepted steps or a fresh bounded-correction verification.
- Internal tolerances: `ftol=None`, `xtol=1e-11`, `gtol=1e-14`.
- Repeats: one unfinished fit per failure example, targeting a different model
  in the fixed order rotating globe, zero-field globe, disc; deterministic fallback
  to the first unfinished fit if that example lacks the target model. Use the
  first original processing case available, without looking at costs. Shift each
  normalized saved coordinate by 0.01 toward zero, with zero shifted to −0.01;
  keep all coordinates within the original box.
- Physical assumptions: original nominal-200-Hz clock, `h1_v3_tau60` GPS covariance,
  ±1°/hour constant gyro offsets, original remaining calibration bounds, no field
  removal versus profiled shared removal. Fit all three physical candidates fairly.
- Completed-control agreement: relative objective difference at most `1e-6` and
  per-axis prediction disagreement at most 0.01 m RMS in the common reference metric.
- Repeat agreement: same objective and prediction tolerances; every repeat and
  its primary must converge. Calibration parameter equality is not required.
- Qualification: all planned starts pass numerical checks and all control/repeat
  agreement checks pass. Otherwise report which criteria failed; no automatic rollout.
- One worker, exactly two BLAS threads; no concurrent numerical jobs. No retries,
  no replacement starts, no allowance reset after interruption.
- Preserve original failures and conclusions. New comparisons always abstain from
  calibrated scientific decisions. This does not prove global optima, statistical
  significance, the source of a rotation field, or a sidereal-versus-solar rate.

Build controls and seal sources before preparation. Preparation hashes four compressed
originals but does not decode/integrate them or fit observations. Full original and
extraction-provenance checks occur after exact finite authorization, before fitting.
An expansion to all 41 needs its own qualified method, selection freeze and allowance.
