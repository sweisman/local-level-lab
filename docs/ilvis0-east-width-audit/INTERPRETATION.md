# The remaining width is sensitive to missing tighter future bounds

**The 32 saved support checks reproduce exactly.** In both specified-field
globe cases, the east-coordinate range still contains a substantial allowance
for approximating the future prediction.

| Processing | Current width | Fixed target | Approximation removed for diagnosis only |
|---|---:|---:|---:|
| Zero removal | 1.4546 m | 1.4066 m | 0.9375 m |
| Profiled removal | 1.4798 m | 1.4443 m | 0.9484 m |

The last column is **not a valid prediction range**. It shows that reducing
the future allowance is worth investigating before changing the training
model or physical calibration bounds. It does not establish how much reduction
is attainable.

The lower endpoint in the zero-removal case comes from region 7; the upper
endpoint comes from region 2. Under profiled removal, regions 0 and 1 determine
the two endpoints. All eight regions remain included in each comparison.

Only older future bounds are available at three of those four decisive
endpoints. At the fourth, the direct-source bound is available and is selected.
This supports investigating how to finish the missing tighter future bounds
within a new, finite runtime allowance. It does not guarantee that doing so
will pass the full target: another region may then determine an endpoint.

The next software candidate is to avoid calculating unused endpoint force
certificates while retaining the endpoint rotation state. Exact equivalence
and measured speed must pass separate checks before any new future-bound
comparison. No larger physical calibration domain, relaxed target or new
aircraft fit is proposed.

[Verified saved calculations](README.md) ·
[Complete comparison](../ilvis0-reused-complete-prediction/INTERPRETATION.md).
