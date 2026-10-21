# Connecting the physical source to the training range

The older adapter fails at zero-width points because it assigns no allowance
to arithmetic differences in its reference values. That implementation and
its failures are preserved. The separate rounded adapter passes 38 local
checks, including the point/boundary cases, both packet phases, changed
reference rows and identity rejection. Its
[matched six-source qualification](../ilvis0-rounded-source-controls/INTERPRETATION.md)
also passes. The revised integration passes [all 24 native controls](../ilvis0-source-native-v2-controls/INTERPRETATION.md).
Complete prediction ranges remain a further gate.

## Reference differences

The initial physical force is the calibrated first sample transformed by the
mount rotation. Exact-rational rotation and derivative intervals bound its
ideal reference value and derivatives. The calculation includes rounding of
normalized parameter products and gravity subtraction, then compares these
with the stored center and all 27 stored derivative columns.

The maximum center-plus-row discrepancy over the stated parameter box supplies
an explicit padding for the training-derived source range. It is calculated
from arithmetic, rather than chosen as a comparison tolerance. The original
nonlinear cap must remain sufficient. A failed cap check rejects the candidate;
it does not enlarge the physical calibration bounds or shared-error columns.

The nonlinear-cap check uses the usual rotation and calibration expansion.
For literal installation matrix \(I_0\), angle change \(d\), initial force
\(f_0\), force change \(D_f\), and calibration remainder \(R_f\), a norm bound is

\[
\|I_0\|\left(\tfrac12 d^2\|f_0\|+
\min(2,d)D_f+R_f\right).
\]

The rotation derivative intervals come from differentiated scalar Rodrigues
series, with explicit first-omitted-term bounds. Independent matrix Fréchet
series check the implementation. The installation matrix's norm is bounded
without repairing it into a different rotation.

## Physical closure and stated rows

The padded training range is intersected with the separately qualified physical
source interval. The norm identity constrains the body departure before either
source is converted to floating-point reference values. A contradiction remains
an error.

For each supplied affine row, the error allowance contains the entire physical
value interval plus that row's range over the parameter box. Known reference
center differences are included explicitly. An old Taylor radius is never
silently reused about a different row. This remains valid for deliberately
changed rows, although it can produce wider bounds.

The [finite qualification](../ilvis0-rounded-source-controls/PLAN.md) preserves
the saved training certificates and seals selected bounds before examining
generated truth values. Full native integration, useful complete prediction
ranges and observational coverage remain later gates.
