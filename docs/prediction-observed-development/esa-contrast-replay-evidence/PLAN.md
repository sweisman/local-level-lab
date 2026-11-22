# Check the new contrast against fully integrated calibration examples

The [integrated error budget](ESA_INTEGRATED_CONTRAST_SUPPORT_RESULT.md)
gives sufficient error limits for the saved shape contrast. Before
trying to prove those limits over the full parameter boxes, see what the
actual integration does at the four calibration points already logged
by the [linked calibration replay](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md).

Verify and reuse the two original baselines, four physical parameter
vectors and four linked approximations. Rebuild the exact compact
contrast from its saved later taps and the earlier state projection.
Compare the fully integrated and affine position changes directly under
that contrast. Report the signed change in the score caused by the
approximation, the largest implied interval-average velocity difference
on either side of the forecast cut, and the exact outward score interval
for the evaluated coordinate errors. Keep the two points meeting the
original earlier loss rule separate from the two that exceed it. Never
treat the four examples as a certificate over a calibration box.

Use two tasks, each with three native passes, 243,154,080 conservatively
charged packet visits, two score checks and two bound steps. The study
uses two total numerical threads and a 180-second cooperative wall
allowance. Allow one separately charged recovery attempt per interrupted
task under the verified recovery policy. Preserve the original
baselines and require the original score, loss and gate to reproduce
for both perturbations. Freeze the exact input receipts, qualifier and
per-task allowance before starting either task. The study uses no new
fits, reads no later GPS positions and leaves reserved recordings closed.
