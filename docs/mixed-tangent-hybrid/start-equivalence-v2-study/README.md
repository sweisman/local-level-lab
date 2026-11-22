# Fresh generated start-equivalence check passed

The faster model-declared tangent **passed all six generated settings** on a
new 180-second route calculation. Both fixed starts were run for each of the
three physical models and two upstream-removal settings. All 12 paired tasks
passed their own numerical and physical checks. The revised rule also passed
same-start cost agreement, near-minimum start selection and forecast agreement
both across and within methods in every setting.

| Measure | Result | Frozen limit |
|---|---:|---:|
| Complete settings passing | **6/6** | 6/6 |
| Largest cross-method forecast separation | 3.13 × 10⁻⁹ m | 0.01 m |
| Largest within-method forecast spread | 3.13 × 10⁻⁹ m | 0.01 m |
| Settings with different primary starts | 2/6 | Allowed only for near ties with stable forecasts |

The cost rule used the pre-existing near-zero solver ceiling of `1e-8`
sum-of-squares units as its absolute floor, alongside the frozen `1e-8`
relative tolerance. The [method note](START_EQUIVALENCE_V2_METHOD.md) explains
why that floor belongs to this generated near-zero objective. The original
120-second study remains **failed under its own 2/6 rule**; this new result
does not rewrite it.

The [machine report](start-equivalence-v2-result.json) verifies every sealed
artifact and records all six rule outcomes. The
[frozen plan](START_EQUIVALENCE_V2_STUDY_PLAN.md) fixes the geometry,
criteria and limits. The study completed in 1,381 seconds, charging 240 of
4,824 allowed native calls and 1.146 of 20.541 billion allowed packet/query
visits. Its 52 source-bound software and recovery checks passed.

This is **generated-data method qualification only**. It contains no NASA or
ESA aircraft recording, and it does not establish which Earth model is true.
The faster tangent cannot replace the established wide calculation on
observed data until a separately frozen development comparison passes under
an objective-scale rule justified for that observed fit. The seven reserved
ESA flight groups remain closed.
