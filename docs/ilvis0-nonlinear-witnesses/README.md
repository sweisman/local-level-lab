# Can the same observations allow different predictions?

**6/6 pairs checked; 1/6 contain different calibrations.**
0/6 exceed a width target.

These are generated software cases, not new aircraft findings. Each search
uses the original five earlier observations and all original calibration
limits. Future observations are excluded. The results are sampled spreads,
not outer uncertainty bounds or global optima.

| Candidate | Removal | Lower sampled N / E / height spread, m | Outcome |
|---|---|---|---|
| Globe, specified field | None | 0.000 / 0.000 / 0.000 | Same starting calibration |
| Globe, specified field | Profiled | 0.000 / 0.000 / 0.000 | Same starting calibration |
| Globe, zero field | None | 0.000 / 0.000 / 0.000 | Same starting calibration |
| Globe, zero field | Profiled | 0.000 / 0.000 / 0.000 | Same starting calibration |
| Flat disc | None | 0.000 / 0.000 / 0.000 | Same starting calibration |
| Flat disc | Profiled | 3.698 / 1.196 / 0.007 | No target violation found |

In 5/6 cases, both directions returned the same starting calibration.
A zero displayed spread there means the search found no alternative; it is
not zero uncertainty. Earlier accepted probes remain valid.

Displayed values are rounded; target comparisons use exact fractions.
The lower spreads subtract the supplied 0.00001 m per-coordinate
numerical-error allowance from both predictions. This allowance is a test
assumption, not a qualified whole-program error bound. A physical impossibility
claim needs that additional qualification. Finding no large spread proves
neither uniqueness nor useful prediction ranges.

| Search | Native batches | Training-compatible proposals | Stopping reason |
|---|---:|---:|---|
| witness-0-0-negative | 33 | 1/32 | native budget exhausted |
| witness-0-0-positive | 33 | 1/32 | native budget exhausted |
| witness-0-1-negative | 33 | 1/32 | native budget exhausted |
| witness-0-1-positive | 33 | 1/32 | native budget exhausted |
| witness-1-0-negative | 33 | 1/32 | native budget exhausted |
| witness-1-0-positive | 33 | 1/32 | native budget exhausted |
| witness-1-1-negative | 33 | 1/32 | native budget exhausted |
| witness-1-1-positive | 33 | 1/32 | native budget exhausted |
| witness-2-0-negative | 33 | 1/32 | native budget exhausted |
| witness-2-0-positive | 33 | 1/32 | native budget exhausted |
| witness-2-1-negative | 33 | 2/32 | native budget exhausted |
| witness-2-1-positive | 33 | 1/32 | native budget exhausted |

The initial batched values and Jacobians match the saved parent in 12/12 searches.
The first proposed moves predicted training errors of 1.43–67.20 m
even in the local linear calculation; their actual errors were 393.64–1740.07 m.
12/12 linear predictions and 12/12 actual outputs exceed the 1 m training limit.
The next method needs controlled, training-compatible steps
before another full-history search.

All 12/12 saved outcomes are retained; 396 native batches
were charged over 22.39 minutes. An optimizer stopping
without success can still supply a checked point; it cannot establish an optimum.

The 53-stretch comparisons are unchanged. Aircraft prediction uncertainty,
whole-period coverage and the real observation-error law remain unqualified.

[Method and limits](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md) ·
[Previous bound comparison](../ilvis0-long-remainder-feasibility/README.md).
