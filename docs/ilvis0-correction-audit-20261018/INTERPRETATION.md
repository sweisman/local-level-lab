# The local linear solve can return a worse step

The saved center Jacobians reproduce the failed right-side corrections almost
exactly: the normalized step differences are below 2 × 10^-10. The center tangent
therefore contains enough information to reproduce this failure; new native
tangent capture is not the first required step.

For both starts, the bounded solver reports successful termination even though
its proposed correction increases its own affine objective from approximately
**2.444154 to 2.444221**. Taking no step is feasible and has lower cost. This is a
failure of that numerical solve on this narrowly bounded, poorly conditioned
problem, before nonlinear aircraft propagation is considered.

Both center Jacobians have all 27 columns numerically retained, with condition
ratios around **253 million**. Removing only the timing correction for the
diagnostic produces much smaller steps and reduces the affine cost. This does
not justify fixing time in the scientific fit. It identifies the tiny timing
interval and coupled calibration directions as the next numerical target.

The existing fresh native gate correctly rejects the bad steps: the subsequent
position changes reach about 20 mm RMS per axis, above its 1 mm numerical limit.
Those stopping limits should remain unchanged.

The next candidate should rescale the affine parameter box, preserve every
physical direction and bound, and explicitly reject a proposed affine solution
that is worse than a known feasible reference. Qualification needs known bounded
optima and these exact saved systems. Success on linear systems alone cannot
qualify the nonlinear archival comparison or change **51/0/2**.

[Saved-system report](README.md) · [Next analyses](../NEXT_STEPS.md).
