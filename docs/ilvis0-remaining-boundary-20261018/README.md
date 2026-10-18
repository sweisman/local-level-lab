# Boundary checks for the remaining time-alignment fits

Four completed zero-field-globe fits agree closely on repeat but fail their full
numerical stopping checks. This study tests their immediate timing neighborhoods
under the same physical assumptions. It uses both processing cases of stretch
`0e73879f98c3b701fd7c42df`, with fresh controls first.

The [saved-endpoint audit](../ilvis0-remaining-free-time-audit-20261018/README.md)
places the endpoints about 12 and 61 nanoseconds from integration boundaries.
Without fitted field removal, the timing coordinate fails stationarity. With
removal fitted, a fresh correction fails cost and stationarity checks, although
position changes remain below the existing limits. The two issues are recorded
separately.

The existing source-preserving search checks nearby packet transitions, then
applies the unchanged full two-sided gate. It cannot accept an endpoint merely
because predictions repeat or a local slope changes sign.

The finite scope is **six diagnostic identities, 110 native calls maximum,
zero nonlinear optimizer starts and four total threads**. No retry or wider
rollout follows automatically. At recent speed, the ceiling is about 50 minutes.

Findings remain **50 globe / zero flat / three unresolved** until a successful
check also passes the required saved companion/model review.

[Finite plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).

Progress is available through `~/venv/bin/python analysis/status.py`.
