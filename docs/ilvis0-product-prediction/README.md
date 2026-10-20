# Prediction with joint rotation relationships

48/48 sectors pass correctness.

All groups meet the unchanged twofold width target: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.1963 / 1.5583 / 1.0339 | 1.0000 / 1.0000 / 1.0000 | No |
| Globe with specified field / profiled | Yes | 1.2818 / 1.6333 / 1.1203 | 1.0000 / 1.0000 / 1.0000 | No |
| Globe with zero field / zero | Yes | 0.9106 / 0.9761 / 0.7291 | 0.9999 / 0.9999 / 1.0000 | Yes |
| Globe with zero field / profiled | Yes | 1.0659 / 1.1220 / 0.8852 | 1.0000 / 0.9999 / 1.0000 | Yes |
| Flat disc / zero | Yes | 0.6691 / 0.2095 / 0.5155 | 0.9998 / 0.9993 / 1.0000 | Yes |
| Flat disc / profiled | Yes | 0.8587 / 0.2687 / 0.6987 | 1.0000 / 0.9999 / 1.0000 | Yes |

Elapsed 156.1 seconds. Reconciled 288/288 LP reservations and 1152/1,152 exact support reservations across passing cases. No new native prediction, integration bound, physical oracle or original-aircraft read.

All original 51 coordinates, native expressions and error allowances remain. The 27 extra coordinates are arithmetic products, not physical sensor parameters. Necessary joint relationships do not establish physical realizability or calibrated observational coverage. These generated controls do not change the 53 aircraft findings.

[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-rotation-product-controls/INTERPRETATION.md) · [Previous widths](../ilvis0-conditioned-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
