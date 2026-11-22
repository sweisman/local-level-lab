# Weak-direction curvature reached its wall limit in the generated flight

The candidate attempted **181 training tangent calls** on the
24-second generated flight before the fixed **210-second** limit.
It saved no final fit or later-position forecast. The sealed
trust-region reference for the same case passed in **10 training
evaluations**. The matched flight qualification failed.

All 200 allowed training evaluations and their associated operations
were reserved before the start. The recorded attempted work was
4,353 covariance-construction calls plus 181 training tangents.
No forecast began. There is no candidate training-cost difference or
withheld-position spread to report. The earlier reference forecast
and the eight small-control results remain valid within their scope.

The [small generated gate](WEAK_TANGENT_CURVATURE_RESULT.md) passed
with two-dimensional tangents. This flight's saved reference tangent
has 26 coordinates. Estimating all weak directions can require 30
new tangent calls for one step at that point. A different design
should derive curvature from calls the solver already makes, or use
a smaller set of directions and verify what that approximation loses.
Repeating this completed run would not establish a lower work cost.

Five focused software checks passed. The original wall-limit failure
and charged work are sealed. No aircraft measurement or reserved
flight was opened. The observed solver remains the original one.

[Frozen plan](WEAK_CURVATURE_FLIGHT_PLAN.md) ·
[Sealed disposition and native work](weak-curvature-flight-result.json)
