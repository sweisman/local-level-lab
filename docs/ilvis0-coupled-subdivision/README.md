# Prediction ranges over smaller calibration boxes

192/192 registered child calculations passed.

All groups meet the unchanged twofold width target: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Fraction of parent width | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.1960 / 1.5582 / 1.0295 | 0.9997 / 0.9999 / 0.9962 | No |
| Globe with specified field / profiled | Yes | 1.2815 / 1.6332 / 1.1165 | 0.9998 / 0.9999 / 0.9966 | No |
| Globe with zero field / zero | Yes | 0.9106 / 0.9760 / 0.7235 | 1.0000 / 1.0000 / 0.9929 | Yes |
| Globe with zero field / profiled | Yes | 1.0659 / 1.1220 / 0.8799 | 1.0000 / 1.0000 / 0.9946 | Yes |
| Flat disc / zero | Yes | 0.6691 / 0.2095 / 0.5085 | 1.0000 / 0.9998 / 0.9875 | Yes |
| Flat disc / profiled | Yes | 0.8587 / 0.2687 / 0.6905 | 1.0000 / 0.9999 / 0.9890 | Yes |

Elapsed 663.2 seconds. Published ranges union every surviving child and all eight original yaw sectors. Shared-boundary children are retained; they do not create independent observations. All original radii, expressions, parent constraints and 78 coordinates remain.

Reconciled 192/192 cover audits, 192/192 setups, 384/384 interval maps, 192/192 coupling audits, 192/192 contractions, 1152/1,152 LP proposals, 4608/4,608 exact support checks and 192/192 truth audits.

This is a generated 7.2-second method comparison. No native prediction or propagation bound was recomputed, no original-aircraft file was read and no observed model was fitted. Full-flight usefulness and observational coverage remain separate gates.

[Frozen scope](PLAN.md) · [Parent comparison](../ilvis0-coupled-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
