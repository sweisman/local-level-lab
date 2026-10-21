# Source-reference arithmetic: next qualification

The older point-domain regression remains open in all 18 tested combinations;
its strict expected failures preserve that implementation's limitation. A
separate [rounded adapter](ROUNDED_ADAPTER.md) passes 38 local checks, including
the point/boundary cases. The [physical source stream](../ilvis0-source-value-controls/INTERPRETATION.md)
also passes all six complete-prefix qualifications. The
[matched training transfer](../ilvis0-rounded-source-controls/INTERPRETATION.md)
is complete, with all six cases passing. The revised integration now passes
[all 24 native controls](../ilvis0-source-native-v2-controls/INTERPRETATION.md).

## First component

`lll.ilvis0_rotation_roundoff` now encloses an ideal rotation at a literal
reference angle using exact rational arithmetic. It uses Rodrigues' formula
with the scalar series

\[
a(q)=\sum_{k=0}^{\infty}\frac{(-q)^k}{(2k+1)!},\qquad
b(q)=\sum_{k=0}^{\infty}\frac{(-q)^k}{(2k+2)!},\quad q=v^Tv.
\]

After the terms decrease, the first omitted term bounds each alternating
series tail. For each matrix entry the error is bounded by the corresponding
skew-matrix entry times the first tail, plus its square's entry times the
second tail. All polynomial and tail calculations use rational numbers;
conversion of reported errors rounds outward. The finite supported angle norm
is eight radians. The internal stopping target controls calculation cost; the
actual tail remains in the returned bound.

Independent matrix-power-series tests check zero, small, signed, large and
subnormal inputs. This is a reference-center component, not a complete source
roundoff certificate or a replacement for the native point map.

## Calibration component

`lll.ilvis0_calibration_roundoff` now bounds each corrected increment
`(raw − bias × period) / (1 + gain)`, optionally divided by its period.
Exact corner values bound the complete bias/gain box. The affine-error bound
also includes the rational gain remainder, the supplied reference-center
discrepancy and differences in the stated bias/gain rows. Binary64 conversion
of supplied rational centers or rows is included explicitly.

Five local checks cover both increments and rates, fixed-point arithmetic
errors, deliberately changed reference rows, invalid domains and nonbinary
reference rows. These checks do not yet establish a complete source bound.

## Remaining source work

1. Complete the [best-baseline screen](../ilvis0-source-range-preflight/PLAN.md),
   preserving exact centers, coefficients and common-error bindings before
   intersecting any allowances.
2. Freeze the complete prediction comparison over all required orientations
   and calibration boxes. Retain the original usefulness targets and known-input
   containment checks.
3. Begin observed withheld prediction only after that gate passes.

The six-source runtime screen is complete. Complete prediction widths and
observed withheld prediction remain separate, unpassed gates.
