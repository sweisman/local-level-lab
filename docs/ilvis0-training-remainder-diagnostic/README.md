# Last-training-epoch allowance comparison

0/6 source, center and coefficient checks passed.

| Candidate / removal | Check passed | Original half-width N / E / height (m) | Recomputed half-width (m) | Fraction of original |
|---|---|---:|---:|---:|
| Globe with specified field / zero | No | 0.14630 / 0.19885 / 0.14218 | 0.14379 / 0.19452 / 0.14218 | 0.98281 / 0.97822 / 0.99998 |
| Globe with specified field / profiled | No | 0.15876 / 0.20929 / 0.15465 | 0.15624 / 0.20496 / 0.15464 | 0.98416 / 0.97931 / 0.99998 |
| Globe with zero field / zero | No | 0.10393 / 0.11713 / 0.09640 | 0.10142 / 0.11280 / 0.09640 | 0.97583 / 0.96307 / 0.99999 |
| Globe with zero field / profiled | No | 0.12646 / 0.14155 / 0.11896 | 0.12395 / 0.13723 / 0.11895 | 0.98013 / 0.96943 / 0.99999 |
| Flat disc / zero | No | 0.06365 / 0.02338 / 0.06304 | 0.06365 / 0.02312 / 0.06304 | 1.00000 / 0.98867 / 1.00000 |
| Flat disc / profiled | No | 0.08996 / 0.03169 / 0.08935 | 0.08996 / 0.03143 / 0.08935 | 0.99999 / 0.99163 / 0.99999 |

Elapsed 79.1 seconds. Six fixed generated cases use the same original reference and last training epoch. No training constraint was replaced, and no future prediction, original-aircraft read or model fit was performed. These are method allowances, not measured aircraft errors. A tighter complete prediction remains a separate test.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
