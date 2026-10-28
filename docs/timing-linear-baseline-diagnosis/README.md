# Saved bounded linear calculation checks

**4 saved linear calculations were independently checked.**

The two failed calibration cases return higher predicted costs than a feasible zero step. The matched earlier controls do not. This isolates a problem in the bounded linear calculation; it does not establish the cause of every earlier numerical failure.

| Saved fit | Starting cost | Returned linear cost | Worse than zero step? |
|---|---:|---:|---|
| Earlier control, start 0 | 228.314752962 | 228.314752962 | No |
| Earlier control, start 1 | 228.314752962 | 228.314752962 | No |
| Failed case, start 0 | 201.208295996 | 201.221747525 | Yes |
| Failed case, start 1 | 201.208295996 | 201.221747525 | Yes |

The runner accepted 0/4 task envelopes. A schema error omitted the required top-level abstention field after the calculations were saved. Their hashes, scalar arithmetic and four charged solves were checked separately. No calculation was rerun, and the rejected envelope labels remain unchanged.

Every calculation retains all 26 nuisance directions and the original physical bounds. It uses the exact saved final linearization; it is not a native replay at a different anchor. No original fit is relabeled, no calibration threshold is established and validation stays blocked.

Next: reproduce the linear-solver failure with an independent known-answer problem, then qualify a correction before any new campaign.

[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
