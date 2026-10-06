# Completed second development pilot — 2026-10-06

All **1,000 authorized development attempts** completed in approximately **3h24m**
(12.26 seconds per attempt). There were zero analysis failures, 905 eligible flights,
and no diagnostic rejections of the generating model. No empirical thresholds were
estimated and no independent validation ran. The shared seeds are paired across cells;
this is not 1,000 independent observations of one null distribution.

The frozen configuration uses the 75-minute protocol, SPP sensor, dynamic crab and bias,
axis/segment weights, forward-axis uncertainty, moving blocks of length 15, 20 nonlinear
bootstrap replicates and a preregistered 10% relative rank-boundary margin. Seeds
600300–600466 are disjoint from the first pilot. See `manifest.json` for the exact source,
configuration, eligibility policy and numerical environment freeze.

| Truth / scenario | Attempts | Eligible | Eligible rank 2 | Valid bootstrap | Eligible three-model separation |
|---|---:|---:|---:|---:|---:|
| Rotating globe / mixed bias | 167 | 166 | 166 | 167 | 166 |
| Rotating globe / wind | 167 | 144 | 144 | 167 | 144 |
| Still globe / mixed bias | 167 | 166 | 166 | 167 | 166 |
| Still globe / wind | 167 | 132 | 132 | 165 | 132 |
| Flat disc / mixed bias | 166 | 161 | 148 | 166 | 148 |
| Flat disc / wind | 166 | 136 | 128 | 166 | 132 |

Each cell has zero conditional diagnostic false rejections among eligible flights.
Three-model separation means retaining the generating model and rejecting both alternatives
under the uncalibrated diagnostic rule. Its total is 888/905 eligible flights. This is not
validated power or a demonstrated 0.0027 false-rejection bound.

Ranks were 936 rank 2, 62 rank 1 and two rank 0; 884 rank-2 flights were eligible.
`rank-sweep-narrow.json` changes the cutoff by ±10%: 53 flights change rank, and none is
eligible under the frozen margin gate. The wide development sweep changes rank in 942 flights.
These sensitivity calculations use saved singular values without new fits.

Overlapping exclusions affected 95 flights: 72 design-contrast failures, 53 unstable-rank
exclusions, 11 WMM-selection exclusions, two missing identifiable subspaces and two invalid
bootstraps. The two bootstrap-invalid records are still-globe/wind seeds 600411 and 600445,
both rank 0 and excluded. Bootstrap validity is therefore 998/1,000, not universal.

The magnetic watchdog flags 120/500 wind flights and 3/500 mixed-bias flights despite zero
injected mount creep. All 72 design failures coincide with those flags (69 wind, three mixed
bias). It removes 669 wind bins and 12 mixed-bias bins across the three truths. Rates remain
apparent yaw change with unresolved crab/slip ambiguity; the protective exclusions are retained.
`magnetic-summary.json` preserves the six cells separately.

| Pairwise comparison | Informative | Decisions | Abstentions |
|---|---:|---:|---:|
| Rotating globe / still globe | 926 | 922 | 78 |
| Rotating globe / flat disc | 924 | 626 | 374 |
| Still globe / flat disc | 905 | 887 | 113 |

Pairwise evidence produced 888 correct three-model winners, zero incorrect winners and
112 abstentions. There were no diagnostic rejections of the generating model in an eligible
pair containing that model. An informative pair can still abstain if the statistic does not
select a winner, especially when the generating model is outside that pair. Pairwise and
pooled-summary thresholds still require their own calibration and independent validation.

## Saved artifacts and remaining work

- `campaign.json.gz` and `records.jsonl.gz`: lossless full results and completed checkpoint journal.
- `manifest.json`: original immutable freeze; `rank-sweep.json`, `rank-sweep-narrow.json` and
  `magnetic-summary.json`: generated development diagnostics.
- `status.json`, launch/log/lock and uncompressed results: local worker bookkeeping.

The worker is complete. **Do not resume it or rerun attempts.** On a fresh clone, use the
compressed records/results for review; no worker or original home-directory tracks are required.

The worst observed eligible rank-2 fraction is 128/166. At the existing goals of 29,285 accepted
calibration and 33,169 accepted validation flights per truth/scenario cell, that point estimate
implies 37,979 calibration plus 43,017 validation attempts per cell: **485,976 combined attempts**,
about **69 serial days** at this pilot's runtime, before reserve. This assumes acceptance and
runtime persist; it is not a guaranteed compute budget. The older frozen proposal retains its
historical cost estimates and must be refreshed before any launch.

Next: review the geometry/rank/selection envelope, revise and freeze source/configuration/policy/
environment, obtain a new compute budget, run fresh primary and pairwise calibration, then
freeze independent validation with the actual thresholds. No additional flights, calibration,
validation, production promotion or git operations are authorized by the completed pilot.
