# What the global increment controls establish

All **30 identities passed**, covering 1,920 generated probes and 12,726 charged
reference/value evaluations. Twelve calibration cases check complete bias/gain
boxes; twelve rotation cases check rotation and integrated-force maps; six
histories check shared calibration over 1, 7 and 31 packets. No archive originals,
optimizer starts or native-engine evaluations were used.

The largest sampled remainder reaches the analytic calibration bound, rather
than exceeding it. Packet and history remainder/bound ratios are at most about
0.948 and 0.894. Repository/reference discrepancies are below 6e-14 in these
short controls. The comparison tolerance does not prove a long-record rounding
bound.

The useful change is methodological: the implementation now has global bounds
derived from the declared calibration region and rotation integrals. Their size
is not chosen from a favorable sample of local perturbations. The bounds retain
joint angle/velocity effects and calibration shared across packets.

## Important distinction from the full prediction engine

The body-preintegration helper integrates constant rotating body force with
rotation/J/K factors. The main native prediction engine instead uses midpoint
force rotation, local-frame transport, Coriolis dynamics and candidate-dependent
geographic rates. This study does not assert that those are the same map.

Reciprocal calibration and exponential rotation bounds transfer as components;
the complete native local step, geographic conversion, processing/removal term,
lever arms and uncertain receiver timing still need their own propagation.
The initial-attitude region is also broad, including a full yaw range. A valid
global bound can be wide; passing these controls does not establish useful
prediction precision.

The new component therefore remains outside the archive prediction gate until
all required terms and numerical errors are covered. Missing terms continue to
produce unsupported uncertainty. No original finding or failure is relabeled.

[Results](README.md) · [Proof and limits](PLAN.md) ·
[Next native step](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
