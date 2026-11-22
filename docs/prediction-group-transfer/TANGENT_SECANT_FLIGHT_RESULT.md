# Trial-tangent curvature passes its first generated flight comparison

The candidate passed the fixed numerical and physical accuracy
gates on the matched 24-second generated globe case. It used **49
training tangents** and recorded 24 curvature updates. The sealed
trust-region reference used **10**. The [previous probe-based
candidate](WEAK_CURVATURE_FLIGHT_RESULT.md) ran out of time before
saving a forecast.

| Matched test | Observed difference | Allowed |
| --- | ---: | ---: |
| Largest separation between the two withheld position paths | 0.00000356 m | 0.10 m |
| Absolute training cost difference | 8.10 × 10⁻¹¹ | 0.01 |

These differences compare two forecasts. The candidate's actual
errors against the eight withheld generated positions were 2.91 m
horizontal RMS and 0.188 m height RMS. The test saved the forecast
before revealing those positions. The input binding matches the
sealed reference.

The 49 calls reconcile to the initial tangent, trial evaluations
and fresh stopping evaluations. The candidate used zero separate
derivative probes and no generated residual-increment formula.
The worker finished in about 91 seconds within the fixed
210-second limit. Eight focused software checks passed.

This qualifies one specified-field globe fixture. The zero-field
globe and disc cases still need matched generated tests. The
baseline aircraft solver, numerical dispositions and reserved-flight
policy remain unchanged. No observed flight or reserved group was read.

[Frozen plan](TANGENT_SECANT_FLIGHT_PLAN.md) ·
[Verified fit and forecast comparison](tangent-secant-flight-result.json)
