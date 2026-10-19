# Fixed-point diagnosis of the three horizontal repeat failures

The saved-only audit finds three failed IMU21 repeat pairs despite passing
individual fits. The two zero-field globe cases have timing offsets separated
by about 19 ms. The unsubtracted flat pair has matching timing and costs but
misses the 1 mm prediction-RMS limit. Both linear correction formulations are
feasible and predict negligible further improvement at the globe endpoints.

## Fixed points and controls

Use both endpoints of all three failed pairs, with no interval/model selection
changes. For each of these six endpoints evaluate exactly:

1. The saved center.
2. The center with the single largest normalized primary/repeat coordinate
   difference replaced by its counterpart's value. This is timing in the two
   globe cases and gravity correction in the flat case; freeze this choice.
3. The midpoint of the complete primary/repeat parameter vectors.
4. The saved range-scaled full affine correction from the completed audit.

Two control identities are the IMU8 unsubtracted specified-field globe primary
and repeat. Each receives a center reproduction and its saved affine correction.
Every point retains the full parameter vector and original physical bounds.

## Frozen allowance and interpretation

- **Eight identities /28 native tangent evaluations maximum**, zero optimizers.
- Four numerical threads; fifteen minutes including compilation and extraction.
- Preserve original data, assumptions, physical bounds, covariance and scores.
- Freeze point vectors, sources, parent receipts, environment and originals.
  Charge each unique point before calling native code; save atomic hashed full
  predictions and projected residual/Jacobian arrays under exclusive locks.
- Every center must reproduce its saved residual/Jacobian before its other points
  are evaluated. Keep failures and unused allowance; never retry or restart.
- Save scored horizontal and unscored vertical differences. Publication makes
  no integrations. No fit/repeat label, production gate or 53-stretch tally changes.

These are probes, not a new optimizer or a proof of a global optimum. A more
favorable probe can justify a separately frozen recovery method; it cannot
retroactively pass a failed repeat comparison.
