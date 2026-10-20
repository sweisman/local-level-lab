# Saved-baseline transport comparison

**4/6 generated-source comparisons produced compatible completed bounds.**

Both zero-field globe cases reached the unchanged 120-second per-bound limit. All six identities remain charged; the failed cases will not be retried. The four completed cases preserve their source identities, reference centers, all coefficient matrices and verified training conditioning.

| Candidate / removal | Result | Fresh / old allowance N / E / height |
|---|---|---:|
| Globe with specified field / zero | Matched | 0.85959 / 0.96576 / 0.89283 |
| Globe with specified field / profiled | Matched | 0.87390 / 0.96585 / 0.90370 |
| Globe with zero field / zero | time allowance exhausted | unavailable |
| Globe with zero field / profiled | time allowance exhausted | unavailable |
| Flat disc / zero | Matched | 0.95358 / 0.98001 / 0.92661 |
| Flat disc / profiled | Matched | 0.96328 / 0.98404 / 0.94548 |

Charged 6/6 bounds and 19200/19,200 bound packet-steps. All 36/36 support reservations and 36/36 verified supports are retained, including failed bounds. Elapsed 665.24 seconds.

The specified-field cases reduce north allowances by about 13–14%, east by about 3.4%, and height by about 10%. These are tighter numerical error allowances, not improved aircraft measurements or completed full-sector prediction ranges. The complete usefulness test remains open.

The next task is a finite runtime diagnosis before another long comparison. The tighter norm-constrained body-source interval is not installed. No native trajectory, LP proposal, original aircraft data, protected ESA data or optimizer was used.

[Frozen scope](PLAN.md) · [Next task](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
