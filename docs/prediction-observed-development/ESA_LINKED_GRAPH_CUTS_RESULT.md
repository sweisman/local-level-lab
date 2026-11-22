# Linking calibration terms during the search barely changes the ESA bound

The verified combined bound for how far calibration can move the two
zero-field forecasts remains **53.04 units**. The forecast separation is
**25.41 units**. The new calculation reduced the bound by about 0.00046 units,
so it still leaves open whether calibration can erase the separation.

| Candidate | Calibration ranges | Earlier upper bound | New upper bound |
|---|---:|---:|---:|
| Zero-field globe | 5 | 20.637250 | 20.636795 |
| Zero-field disc | 6 | 32.401100 | 32.401099 |

The search proposed 15 physical constraints per range. Only two of 165
excluded the proposed point. Both came from the earlier residual directions
in one disc range. The other proposals lay inside the corresponding bound
over the whole range, even when the proposed lifted terms differed from the
physical ones. All 55 extra earlier-loss constraints excluded their proposed
points, but the remaining outer region still allowed nearly the same forecast
scores. Exact arithmetic reproduced every recorded cut decision.

The result shows where this method loses precision. The bounds allow too much
variation across whole calibration boxes to turn most physical discrepancies
into useful constraints. The two verified physical points from the
[full integration](ESA_LINKED_PHYSICAL_REPLAY_RESULT.md) remain well below the
forecast gap. A global guarantee still needs a sharper calibration bound and
a bound on the full integration error. Prediction-error coverage on independent
flights remains open.

All 11 tasks completed in 128 seconds on two one-thread workers. Three focused
software checks passed. The run used 286 charged operations, with zero new
fits, integrations or reserved-flight reads.

[Frozen method](ESA_LINKED_GRAPH_CUTS_PLAN.md) ·
[All range bounds](esa-linked-graph-cuts-result.json) ·
[Verified evidence](esa-linked-graph-cuts-evidence/README.md)
