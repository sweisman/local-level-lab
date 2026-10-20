# Check the source reference map and its usable error bound

Use the same six generated sources and sector-4 domains as the completed
[value preflight](../ilvis0-source-norm-preflight/README.md). No aircraft data,
ESA confirmation data, optimizer starts or full trajectory predictions are used.

For `A=R f` and `B=R(P−I)f`, expose a source-only calculation using the unchanged
native tangent code's Dual arithmetic, calibration and exponential primitives.
Independently compute all 27 columns using quaternion rotation values and the
analytic right Jacobian of the rotation exponential. The native exponential's
small-angle polynomial remains unchanged; record numerical discrepancies rather
than normalizing matrices or silently changing the frozen implementation.

Use the native clock branch: at an exact packet endpoint, use the preceding
packet's partial-step derivative. Record the selected packet, query time and
distance to its boundaries. A branch-specific coefficient at a kink is not a
unique two-sided derivative. Unused columns remain present as zeros.

Local deterministic tests compare against a third implementation based on
complex-step matrix exponentials, check a discontinuous packet slope, nonuniform
periods, support rejection, signed calibration and an exact rational affine bound.
Six frozen source identities then each receive one native source reference and
one independent reference calculation. Compare 162 value/coefficient entries per
identity, plus its six values; coefficient
agreement uses absolute tolerance 2e-10 and relative tolerance 2e-8. Value agreement
uses absolute tolerance 1e-10 m/s². These numerical tolerances do not certify
whole-program floating-point enclosure or observational uncertainty.

For the already sealed vertical interval `[l,u]`, native center `c` and native
row `J`, compute with exact rational arithmetic

`max(|l−c|, |u−c|) + Σ |Jj| max(|lowerj−centerj|, |upperj−centerj|)`.

This bounds deviation from that specified affine row for the mathematical
source map. It does not require assuming the row is an exact derivative. Compare
against the saved original body-departure remainder before developing another
full propagation candidate. Preserve both the value interval and baseline. A
failed improvement target is a useful negative result, not permission to retry.

Finite execution allowance: six identities, six reference setups, six compiled
source evaluations, six independent reference calculations, and six exact
affine-radius comparisons. Reserve 1,600 packet visits for each native and each
independent prefix (19,200 total). Native source calls are charged separately
from full-trajectory calls; the latter remain zero. Four workers, one numerical
thread each, cooperative wall ceiling 180 seconds, no retries or extensions.
Compiler, source, inputs, environment and allowances are frozen before launch.

Passing coefficient checks qualifies this source component only. Native
integration and a complete prediction comparison remain separate gates, and
observed fitting remains blocked until the broader prediction method qualifies.
