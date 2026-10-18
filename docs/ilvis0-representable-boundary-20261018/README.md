# Representable timing probes

Two endpoint checks stopped because their timing branches were narrower than a
fixed minimum-spacing guard. The [saved-clock audit](../ilvis0-narrow-boundary-audit-v2-20261018/README.md)
confirmed that the proposed side points still occupy distinct, correct clock
states. This separately frozen numerical candidate tests that geometry directly.

The candidate requires distinct points inside each exact adjacent interval,
at least eight floating-point spacings from the knot, and matching clock states.
It retains the original cost, stationarity, continuity, physical-position,
source-preservation and repeat limits. The earlier failed checks remain failed.

Known-answer controls must pass before observed work. The subsequent diagnostic
has **four identities: two fresh controls and two unsubtracted endpoints**, with
**58 native calls maximum, zero nonlinear optimizer starts and four threads**.
At recent speed, the ceiling is about 25 minutes. The already-passing profiled
pair is preserved for later saved review and is not run again.

The public tally remains **50 globe / zero flat / three unresolved**. A successful
diagnostic still needs the required companion/model review.

[Finite plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).

Progress is available through `~/venv/bin/python analysis/status.py`.
