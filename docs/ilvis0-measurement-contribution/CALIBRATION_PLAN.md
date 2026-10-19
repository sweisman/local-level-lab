# Calibration-aware channel controls

This local-calibration design is implemented and its 72-case matrix is complete.
The [subsequent nonlinear study](../ilvis0-scalar-nonlinear-controls-20261019/INTERPRETATION.md)
does not qualify the whole diagnostic for observed use. Current pending work is
collated under C02/C03/C04 in the [authoritative roadmap](../ANALYSIS_ROADMAP.md).

The constant-gain control rules out treating fixed-calibration scalar separation
as sufficient information. The calculation below measures the part of a
force-magnitude difference outside a local calibration tangent space.

## Defined calculation

For a constructed recording, keep one calibration vector across all epochs:
three dimensionless acceleration gains, three acceleration offsets in m/s²,
and one gravity adjustment in m/s². Use the existing exploratory bounds
unchanged (±0.15 gain, ±0.25 m/s² offset and ±0.05 m/s² gravity).

At zero corrections, the residual is measured body-force magnitude minus the
candidate's required-force magnitude. Differentiate the scalar residual with
respect to all seven coordinates, scale columns by their bounds, and report the
complete singular spectrum. Keep all seven columns, including dependent ones.
Project the residual onto the orthogonal complement with an explicit relative
SVD tolerance of 10⁻¹⁰. No covariance or calibrated information/power is implied.

Report the local projected residual, minimum-norm linear correction, whether
that correction lies within the bounds, and its actual nonlinear residual when
feasible. A projection can remove more than a bounded nonlinear calibration
can realize. A surviving local residual likewise does not rule out another
nonlinear solution. Both limitations must accompany the numbers.

## Verification before any new study

Ordinary deterministic unit tests check independent finite-difference
derivatives, exact affine projection, rank deficiency, bound checks, invalid
inputs and failure at zero force. Constructed straight and changing-motion
examples are mathematical controls, not observed fits. They use no archive
files, native integration, fused attitude or optimizer.

This step introduces no observational budget and does not alter completed
freezes. A later trajectory matrix needs its own finite frozen allowance. A
recorded-data comparison still requires nonlinear calibration ambiguity,
quantization, timing, averaging, shared uncertainty and a motion-selected support
policy to be addressed.
