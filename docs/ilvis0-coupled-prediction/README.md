# Prediction ranges with coupled calibration errors

48/48 sectors pass correctness.

All groups meet the unchanged twofold width target: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Fraction of previous width | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.1963 / 1.5583 / 1.0334 | 1.0000 / 1.0000 / 0.9995 | No |
| Globe with specified field / profiled | Yes | 1.2818 / 1.6333 / 1.1203 | 1.0000 / 1.0000 / 1.0000 | No |
| Globe with zero field / zero | Yes | 0.9106 / 0.9761 / 0.7286 | 1.0000 / 1.0000 / 0.9994 | Yes |
| Globe with zero field / profiled | Yes | 1.0659 / 1.1220 / 0.8847 | 1.0000 / 1.0000 / 0.9995 | Yes |
| Flat disc / zero | Yes | 0.6691 / 0.2095 / 0.5150 | 1.0000 / 1.0000 / 0.9989 | Yes |
| Flat disc / profiled | Yes | 0.8587 / 0.2687 / 0.6982 | 1.0000 / 1.0000 / 0.9992 | Yes |

Elapsed 141.4 seconds. Reconciled 48/48 source setups, 96/96 interval maps, 48/48 coupling audits, 48/48 contractions, 288/288 LP proposals, 1152/1,152 exact support checks and 6/48 truth audits.

The original native expressions, physical bounds, coefficients and error allowances are unchanged. The new constraints preserve the complete static calibration relationship. All 78 coordinates remain; the 27 product coordinates add no physical freedom. Generated truth is checked only after bounds are saved.

These generated 7.2-second cases do not establish full-flight uncertainty or calibrated observational coverage. There were no new native predictions, integration bounds, original-aircraft reads or observed fits.

[Frozen scope](PLAN.md) · [Source-map qualification](../ilvis0-coupled-map-controls/INTERPRETATION.md) · [Previous comparison](../ilvis0-product-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
