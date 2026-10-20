# Joint rotation constraints retain every physical control

All 24 cases pass. The new constraints retain every one of the 1,536 sealed
physical probes and every original coordinate. Exact arithmetic checks 198,144
inequalities and 119,808 coordinate bounds. The completed physical generators
were not rerun; the new checks finished in 43.2 seconds.

The construction relates columns through their inner products, allowing for the
stored mounting matrix's small numerical defect. It introduces 27 arithmetic
product coordinates while retaining all 51 original coordinates and 27 physical
parameters. No new sensor freedom, native integration or observed fit is added.

These are necessary constraints with explicit numerical allowances. The relaxed
products do not prove that every surviving matrix is a physically realizable
proper rotation. Passing these controls also does not establish narrower future
position ranges or aircraft-error coverage.

The [complete saved-prediction comparison](../ilvis0-product-prediction/PLAN.md)
will test usefulness under the unchanged target. The preceding four-of-six-group
result remains preserved.

[Control results](README.md) · [Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
