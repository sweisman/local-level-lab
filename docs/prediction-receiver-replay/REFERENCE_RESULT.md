# Receiver-target references from saved simulator forecasts

The replay recovered **3,432 reference scores** from 286 of the 299
original calibration seeds. Each seed supplies one earlier-selected fit
in each of 12 scenarios. All 286 new tasks passed. The first run's 13
failures remain unavailable in every scenario. An independent check
confirmed all 3,432 start selections against the original training-cost
ledger. The replay ran no fits and opened no aircraft recordings or
original validation cases. [Accounting record](REFERENCE_ACCOUNTING.md)

| Error across the 12 simulated scenarios | Median range | 95th-percentile range |
| --- | ---: | ---: |
| Forecast versus exact simulated positions | 2.76–2.98 m | 4.91–5.57 m |
| Same forecast versus noisy receiver positions | 2.84–3.08 m | 4.90–5.66 m |

Each reference fit uses its own generating model. These ranges describe
position error in the original simulator. Aircraft calibration and
model discrimination require separate tests. The seed IDs are retained
because the scenarios share random draws.

## What the missing seeds cost

With 13 unavailable draws among 299 planned, the smallest possible
rank p-value is **14/300, or 4.67%**. At the illustrated 5% overall
allowance, only the rule requiring all seven groups can reach its
cutoff. Even under that rule, at most one available reference may tie
or exceed a query's score. The resulting minimum scores to exceed
range from 6.13 to 7.71 m across the twelve scenarios. Requiring five
of seven groups would need at least 839 planned references per scenario
at the same unavailable count. These numbers measure the resolution
of this archive. The operational threshold remains open.

The source run charged 10,296 checks and finished in about 20 minutes.
The verification reproduces the seed ledger, scenario counts and
rank arithmetic. The earlier validation cohort and the seven reserved
ESA groups remain unused.
[Replay plan](REFERENCE_PLAN.md) · [Rank plan](REFERENCE_RESOLUTION_PLAN.md) ·
[Reference scores](reference-result.json) · [Rank calculations](reference-resolution.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  ~/venv/bin/python -m lll.prediction_reference_resolution check
```
