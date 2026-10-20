# Can one calibration produce the extreme errors?

6/6 generated cases completed their correctness checks.

This is a software diagnosis of prediction ranges. No aircraft model comparison was rerun.

| Candidate / removal | Exact witnesses | Mapped witnesses inside training region | Collapsed to known anchor | Largest signed-axis change (m) |
|---|---:|---:|---:|---:|
| Globe with specified field / zero | 6/6 | 0/6 | 0 | 70.238593 |
| Globe with specified field / profiled | 6/6 | 0/6 | 0 | 70.211442 |
| Globe with zero field / zero | 6/6 | 0/6 | 0 | 77.755138 |
| Globe with zero field / profiled | 6/6 | 0/6 | 0 | 65.001639 |
| Flat disc / zero | 6/6 | 0/6 | 0 | 66.415855 |
| Flat disc / profiled | 6/6 | 0/6 | 0 | 81.860350 |

Elapsed 13.2 seconds. Reconciled 36/36 LP proposals, 42/42 complete map evaluations and 142,878/246,000 scalar checks.

Each LP point was saved, repaired with exact arithmetic toward its known generated anchor and independently checked. Its 27 physical values were then converted explicitly to binary numbers. All 24 common errors were recomputed from that same calibration; the 27 arithmetic products were rebuilt without clipping. Signed changes retain cancellation between blocks. The known anchor is unavailable to a real prediction method.

A failing mapped point is not a feasible physical example for the saved extreme. A passing point is only a surrogate example, not a global optimum, native trajectory or calibrated interval. Failed proposals and conversions remain without replacements. There were zero new native predictions, integration bounds, original-aircraft reads or observed fits. The 53 aircraft findings are unchanged.

[Frozen scope](PLAN.md) · [Preceding comparison](../ilvis0-product-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
