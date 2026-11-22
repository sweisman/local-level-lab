# The two turning fits stop at repeatable low-cost points

The [finite fixed-point probe](TURNING_FIXED_POINT_V2_PLAN.md) completed both
technical tasks. It made no new optimizer starts and read no observed or
protected recording. The first technical attempt used the wrong directory to
locate its sealed parent and ended before any native call; that failure remains
preserved separately. The corrected run replayed the two saved generated
turning inputs and their original fit points exactly.

| Saved turning case | Original fit | Exact residual/Jacobian repeat? | Relative cost change at full correction | Required maximum |
| --- | --- | --- | ---: | ---: |
| Level | Not converged | Yes | 1.63 × 10⁻⁷ | 1 × 10⁻⁸ |
| Shallow climb | Not converged | Yes | 0.89 × 10⁻⁷ | 1 × 10⁻⁸ |

Both regenerated baseline costs equal the sealed costs exactly. The full
bounded local correction predicts a small reduction but raises the actual
cost by 0.0000349 and 0.0000191, respectively. Every tested positive and
negative fraction of that correction also raises the actual cost. A small
negative fraction falls within the cost-change threshold, but it is not the
full bounded correction that the frozen stopping rule requires. The final
position and stationarity checks pass; the full-correction cost check fails.

This rules out nondeterministic repeat evaluation as the immediate reason
for these two stopping failures. It shows a local linear prediction that is
too optimistic at the tested correction, in a weakly identified calibration
valley. It does **not** establish the global optimum or justify changing the
stopping threshold. Both original turning fits remain nonconverged. The next
gate is an independently generated, known-optimum numerical control comparing
bounded solution strategies on the same turning route, with a new finite
allowance and unchanged scientific inputs.

The sealed result is
`data/generated-turning-fixed-point-v2-20261117`; each task stores its ten
residual/Jacobian sweeps, charged work, source and input hashes. The separate
zero-native-call technical failure is
`data/generated-turning-fixed-point-v1-20261117`.
