# Saved-parameter residual diagnostic

Evaluate the two stretches already selected for the matched solver trial, using the
12 original baseline fits. Each fit receives one nominal-200-Hz prediction and one
packet-header prediction: **24 predictions maximum, zero optimizer starts**. No new
interval selection, calibration freedom, thresholds or model decisions are introduced.

Implementation:

1. Add `analysis/lll/ilvis0_residuals.py` for residual distributions, centered
   autocorrelation and descriptive associations with independent receiver properties.
   Add deterministic controls in `analysis/tests/test_ilvis0_residuals.py`.
2. Add `analysis/tests/ilvis0_residual_diagnostic.py` to verify publication/input/source
   hashes and the numerical environment, reconstruct the original prediction problem,
   save per-epoch coordinate/physical/whitened residuals in deterministic compressed CSV,
   and reproduce saved costs/RMS before interpreting diagnostics.
3. Use a new output freeze at `data/ilvis0-residual-diagnostic-20261010/`. Charge each
   prediction before evaluation in an append-only journal, lock execution, preserve
   atomic hashed outputs and failures, and never retry an interrupted charged identity.
   Verified completed predictions may be repackaged without integration.
4. Publish a plain-language report and reproduction instructions here. Keep original
   baseline and solver-trial evidence unchanged.

Receiver epochs are observations, not independent confirmations. Cholesky-whitened
components are innovations in the declared stacked coordinate order, not physical
metres. Their distribution and autocorrelation are descriptive checks of the assumed
covariance, not a calibrated adequacy decision. Fixed-parameter clock comparisons
are not reoptimized timing alternatives. No held-out prediction test is performed.
No temperature measurement is inferred from elapsed time or flight motion.

The implementation is reviewed locally without agent delegation. Focused tests cover
statistics, integrity failures and bounded/restart behavior; no full campaign is run.
