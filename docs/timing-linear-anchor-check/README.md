# Saved bounded linear calculation checks

**4 saved linear calculations were independently checked.**

All four proposals retain or reduce the feasible anchor objective and report solver success. This checks the revised bounded linear calculation on the matched saved matrices; it does not qualify the complete nonlinear optimizer or establish calibration coverage.

| Saved fit | Starting cost | Returned linear cost | Worse than zero step? |
|---|---:|---:|---|
| Earlier control, start 0 | 228.314752962 | 228.314752962 | No |
| Earlier control, start 1 | 228.314752962 | 228.314752962 | No |
| Failed case, start 0 | 201.208295996 | 201.208295996 | No |
| Failed case, start 1 | 201.208295996 | 201.208295996 | No |

The runner accepted 4/4 task envelopes. Every returned outcome and charged solve is retained; no closed study was restarted.

Every calculation retains all 26 nuisance directions and the original physical bounds. It uses the exact saved final linearization; it is not a native replay at a different anchor. No original fit is relabeled, no calibration threshold is established and validation stays blocked.

Next: reproduce the linear-solver failure with an independent known-answer problem, then qualify a correction before any new campaign.

[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
