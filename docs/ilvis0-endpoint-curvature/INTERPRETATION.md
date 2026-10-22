# A simple derivative average is not the replacement

The saved-derivative check completes correctly, but its approximation is worse
than the existing shared-source expression in most fixed probes.

| Processing case | Shared-source RMS mismatch | Endpoint-average RMS mismatch |
|---|---:|---:|
| Zero removal | 9.07 m | 12.87 m |
| Profiled removal | 45.35 m | 71.41 m |

These compare the same six epochs. The complete 293-epoch derivative check is
also preserved. The endpoint average beats the shared expression for only two
of twelve probes. It will not replace the current method.

Accelerometer gain and offset have the largest grouped terms in this particular
directional-curvature expression. Those terms can interact and cancel; they are
not measured instrument errors or unique physical causes.

The next check will examine curvature **after removing the already modeled
source terms**, rather than approximating their known nonlinear behavior again.
It can use the existing derivatives and the independently checked source-map
derivatives, without new integration or aircraft fitting.

Neither this failed approximation nor the earlier improved sampled agreement
qualifies prediction uncertainty. The original long-record test, physical bounds
and 53-stretch findings remain unchanged.

[Verified results](README.md) · [Next finite audit](NEXT_PLAN.md) · [Current work](../NEXT_STEPS.md)
