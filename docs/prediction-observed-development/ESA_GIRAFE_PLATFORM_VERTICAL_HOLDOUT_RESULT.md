# New vertical-force excerpts agree on the candidate clock offset

Every new excerpt independently placed its strongest match at the proposed
38,474.267-second offset. One of the three passed the predeclared minimum
correlation of 0.70. The clock still fails the qualification rule, and the
shared location of the peaks gives a target for diagnosing force response
and fine timing.

| Excerpt byte offset | Correlation at the fixed time | Next separated peak | Result |
| ---: | ---: | ---: | --- |
| 466,124,214 | 0.467 | 0.451 | Below threshold |
| 931,200,441 | 0.843 | 0.452 | Pass |
| 1,396,276,591 | 0.563 | 0.501 | Below threshold |

The [plan](ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_PLAN.md) fixed the offset
and the minimum correlation in advance. Each search used 112 tenth-second
force values after the overlap and a two-second guard. All three captured
files matched their hashes and verified overlaps, including the file
whose transfer timed out after delivering the requested bytes. The
comparison used one development recording and no reserved groups.

The [terminal receipt](esa-girafe-platform-vertical-holdout-result.json)
has SHA-256 `9f6240a6625bfd586148ac901f14a2e61be9f29e30dc39d89028183065bce54f`.
Manifest SHA-256 is
`77bd279b301c1513a47a3a719e0fec04385fbb7a7eda43c21c1184862c034339`.
All seven charged operations completed locally in 2.9 seconds on one
thread. There were zero model fits and zero new network calls.
The [portable evidence bundle](esa-girafe-platform-vertical-holdout-evidence/bundle.zip)
contains the source freeze, acquisition receipt, outcome and charge ledger.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_vertical_holdout prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-girafe-platform-vertical-holdout-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_girafe_platform_vertical_holdout report
```
