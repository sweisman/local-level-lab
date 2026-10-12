# Rectangular continuation trial: finite proposal

Repeat the same preselected three failure examples and completed October 5 control
under a separate method freeze. Preserve the completed 24-start TRF trial. Start
from the original saved first-pass points, not whichever trial point fits best.

- 15 unfinished primary fits, six control fits, three prescribed perturbed repeats.
- At most 600 fitting tangents and two value predictions per start; **24 starts /
  14,448 native sweeps** total. No retries or replacement starts.
- Rectangular dogbox steps, Jacobian scaling, `ftol=None`, `xtol=1e-11`, `gtol=1e-14`.
- Original gradient threshold `1e-4`, relative cost change `1e-8`, relative residual
  change `1e-6`; a fresh bounded correction verification is mandatory. Callback
  stability alone cannot pass. Unchanged callbacks are not accepted improvements.
- Original physical models, parameter bounds, nominal 200 Hz clock, shared
  `h1_v3_tau60` covariance, ±1°/hour offsets and both processing cases.
- Same predetermined normalized 0.01 perturbations and selection as the original
  recovery proposal, regardless of costs or preferred shape.
- All 24 starts must pass. Control and repeat comparisons require relative objective
  agreement within `1e-6` and every-axis prediction agreement within 0.01 m RMS.
- Save all evaluated costs/step sizes/fresh flags, callback acceptance markers and
  the final residual/Jacobian as a hashed compressed artifact. These records require
  no additional native sweeps beyond the charged final checks. The linear probe
  retains its original conservative early rejection rule.
- One numerical worker, two total BLAS threads. No other numerical work in parallel.
- Journals charge calls before execution. Interrupted starts remain failed and spent.
- Preserve every original outcome; all new outputs abstain from calibrated decisions.
- Same-recording estimate: approximately **10–14 hours at the ceiling**, potentially
  less with warm starts. The smaller previous runtime is not a guarantee.

Software screen: dogbox passed 30/30 controls versus TRF 29/30. A known-answer
near-boundary coupled control reproduces the earlier stopping failure and passes
with dogbox without relaxed tolerances. This is not archive qualification or proof
of global optima. A separately recorded finite authorization is required before
decoding originals or launching observed fits. Success would support preparation
of the separately budgeted all-41 recovery study; failure must be reported.
