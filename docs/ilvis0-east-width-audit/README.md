# Why the two east-coordinate ranges remain too wide

All 32 saved east-coordinate support certificates and all 16 interval endpoints reproduce exactly. No integration, new bound or optimization ran.

| Processing | Actual width | Target | Lower / upper sectors | Future providers | Remainder-removed diagnostic |
|---|---:|---:|---|---|---:|
| Zero removal | 1.454619 m | 1.406598 m | 7 / 2 | earlier-07 / direct-07 | 0.937475 m |
| Profiled removal | 1.479830 m | 1.444322 m | 0 / 1 | earlier-07 / earlier-07 | 0.948422 m |

The final column removes the future remainder algebraically while leaving training constraints and the saved support certificates fixed. **It is not a valid tighter prediction range.** It measures sensitivity to that allowance; it does not prove an attainable improvement or an optimum.

All eight regions in each case were included. No future truth or aircraft residual was consulted. The earlier width failure and all 53 aircraft comparisons remain unchanged.

[Finite audit scope](PLAN.md) · [Source outcome](../ilvis0-reused-complete-prediction/INTERPRETATION.md).
