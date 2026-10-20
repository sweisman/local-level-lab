# Correlated packet-clock controls

24/24 generated controls pass; state: complete.

| Family | Completed | Passed | Exact oracle points |
|---|---:|---:|---:|
| dyadic | 8 | 8 | 632 |
| rounded | 8 | 8 | 1060 |
| variable | 8 | 8 | 1082 |

One common offset is retained across all packets, including selected one-sided boundary slopes. Exact oracle checks include every relevant knot of the inspected prefixes. The supplied upstream time-map remainder remains part of the bound.

This qualifies the mathematical clipped-period map, not an actual instrument clock or whole-program floating-point behavior. No native integration, original files or observed model fitting is performed. Regrouped native propagation needs a separate qualification.

[Frozen controls](PLAN.md) · [Mathematical method and native next gate](../ilvis0-clock-correlation/PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
