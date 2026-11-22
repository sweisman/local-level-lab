# The solver recovers constructed exact targets on turning routes

The [finite known-optimum control](TURNING_KNOWN_OPTIMUM_PLAN.md) completed all
four tasks. It used the same generated turning-route inputs, 26-parameter
native model, noise law, bounds, clock and training operator as the two
nonconverged motion-control fits. It then subtracted the native residual at
each saved feasible point, creating a **constructed zero-cost target**.
This tests the solver's numerical behavior; the constructed target is not an
independent physical truth.

| Route | Start | Converged? | Evaluations | Cost relative to initial | Maximum target-path difference |
| --- | --- | --- | ---: | ---: | ---: |
| Turning, level | Zero | Yes | 8 | 9.94 × 10⁻²¹ | 0.000000106 m |
| Turning, level | Perturbed target | Yes | 8 | 3.83 × 10⁻²⁴ | 0.00000000163 m |
| Turning, shallow climb | Zero | Yes | 8 | 8.90 × 10⁻²¹ | 0.0000000983 m |
| Turning, shallow climb | Perturbed target | Yes | 8 | 3.81 × 10⁻²⁴ | 0.00000000163 m |

All four pass the frozen convergence, cost and 1 mm path criteria. The two
earlier noisy turning fits **still fail** their original stopping checks.
This control argues against a general inability to fit a turning trajectory;
the remaining issue is how the original noisy, weakly identified objective
behaves near its apparent minimum. A separately frozen comparison of
independent bounded solution strategies should test whether either noisy
case has a lower feasible cost or a point that passes the original full
stopping check. If none does, the stopping rule itself needs a separately
qualified revision. No aircraft error-law coverage or Earth-model decision
follows from this control.

The sealed study is `data/generated-turning-known-optimum-v1-20261117`.
It preserves each fit, constructed target, native operator binding, source
and input hashes, and charged work. No observed or protected flight was read.
