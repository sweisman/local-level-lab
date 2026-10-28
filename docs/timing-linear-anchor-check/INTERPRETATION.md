# Feasible initialization resolves the saved linear failure

**All four matched saved-matrix checks pass.** The revised calculation no longer
worsens either failed case, and the earlier controls remain satisfactory. Four
new linear solves were charged in 1.35 seconds; no native calculation, nonlinear
fit or new noise sample was used.

Independent convex controls establish the reference answer without aircraft
data. The previous method fails ten of 24 such cases. The revision passes all
24, a nonoptimal-start check, a test that rejects misleading solver success and
the remaining source-bound checks: 56 in total. Another 90 related software
tests pass separately.

The change starts BVLS at a feasible zero step instead of an unconstrained
solution. It also rejects a worsening result even when the solver reports
success. Every parameter direction, physical bound and scientific acceptance
limit stays unchanged. The version-specific SciPy entry point is covered by
the frozen numerical environment and requires requalification after an update.

This qualifies the tested **linear calculation**, not the complete optimizer or
its native trajectory predictions. The next gate is a fresh full-optimizer
qualification, followed by a separately frozen native trial. The closed
calibration still supplies no threshold; validation remains blocked and the
53-stretch aircraft findings are unchanged.

The [earlier rejected task envelopes](../timing-linear-baseline-diagnosis/README.md)
remain preserved. This new comparison used its own finite allowance.

[Verified report](README.md) · [Results CSV](results.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
