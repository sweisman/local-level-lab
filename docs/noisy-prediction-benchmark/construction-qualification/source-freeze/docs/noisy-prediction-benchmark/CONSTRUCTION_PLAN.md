# Qualify the known-calibration benchmark construction

Test both input-error laws on a generated two-second, 600-packet record.
Use nine query epochs from 0.1 to 1.7 seconds, with six earlier positions and
three future physical-position targets. Supply the true initial state and
known sensor bias/gain, antenna lever arm and latency; estimate no parameters.

The native streaming mean must agree with the already checked wide tangent
calculation within 0.00001 m per coordinate on this short control. Compare it
with the independently generated nominal trajectory as a separate check, at
a fixed 0.01 m maximum 3D error. Compare conditional physical second moments
with a stable, independent dense calculation using the complete innovation
factor. Verify that receiver observation loadings stop at the earlier boundary.

One numerical thread, two compiled libraries and a three-minute cooperative
allowance are permitted. Each case allows 700 native calls, 2,000 packet steps
and 10,000 packet/query visits. Totals are 1,400 calls, 4,000 steps and 20,000
visits. Construction is bounded at 610 generated samples and 600 constructed
intervals per case. No noise draws, optimizer starts, original recordings or
protected groups are used. Unused native prepayment remains charged.

This qualifies benchmark construction, not real-world error amplitudes,
nonlinear coverage or the longer four-setting execution. That execution still
requires its own source/environment freeze and finite allowance.
