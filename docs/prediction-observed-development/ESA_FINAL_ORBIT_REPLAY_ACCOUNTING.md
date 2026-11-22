# Preserve the orbit replay's first launch

The first freeze reached all nine blocks, but a call to the accounting API
omitted a required field before any range calculation. The block results
also omitted the required explicit abstention. The terminal receipt shows
nine failed blocks and zero charged range operations. The sealed block
artifacts record the accounting error on all 1,041 epochs.

The corrected execution uses a separate study identity. It reserves one
operation and the full five evaluations per epoch before entering the
original calculation, even when the comparison finishes in fewer
evaluations. It seals each block with an explicit scientific abstention.
Measurements, interpolator, tolerances, step limits and block boundaries
follow the original plan.

[First launch source and receipts](esa-final-orbit-replay-v1-technical.zip) ·
[Original method and limits](ESA_FINAL_ORBIT_REPLAY_PLAN.md)
