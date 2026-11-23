# Check how much platform orientation would need to change

Reuse the exact two paths, zero-field models and ten supports from the
[horizontal force check](ESA_GIRAFE_HORIZONTAL_WITNESS_RESULT.md). One
path is the original receiver trajectory. The other adds the exact
constructed north–south error that spans the saved score gap. Recompute
the full three-axis mean force over each support and require its
horizontal magnitudes to reproduce the sealed result.

For each paired mean, report the smallest three-dimensional rotation
that makes its two directions coincide, and the force-magnitude
difference that survives arbitrary rotation. Also report the magnitude
of the north–south change and the angle of the rotation axis from local
horizontal, where defined. The scalar magnitude is unchanged by any
sensor orientation. The minimum rotation is a per-support sensitivity,
with no assumed continuity of the orientation error within or between
supports. Use the same receiver path and force calculation in each pair.

For scale only, report the same angles against the 1.5 mrad platform
alignment estimate in Appendix A4 of an earlier campaign. This number
provides no bound on the orientation of the 187a platform.
[Earlier campaign methods](https://doi.org/10.1029/2022JB025921)

Use verified sealed inputs and one local task on one numerical thread.
Allow ten support evaluations with at most 768 quadrature points each,
four predictions per support, and 30 seconds. Use zero new sensor reads,
new fits or reserved-flight reads.
