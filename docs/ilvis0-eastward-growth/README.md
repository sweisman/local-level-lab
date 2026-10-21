# Eastward propagation-allowance growth

6/8 fixed query traces passed exact predecessor checks.

| Source | Query seconds | Departure allowance (m) | Final position allowance (m) | Force allowance (m) | Lever allowance (m) | Final allowance (m) |
|---|---:|---:|---:|---:|---:|---:|
| transform-full-0-0-1-training | 6.0 | 0.173881 | 0.19616 | 0.0222788 | 0.015345 | 0.211505 |
| transform-full-0-0-7-training | 6.0 | 0.17545 | 0.197729 | 0.0222788 | 0.0153465 | 0.213075 |
| transform-full-0-1-1-training | 6.0 | 0.170818 | 0.193097 | 0.0222788 | 0.0189374 | 0.212034 |
| transform-full-0-1-1-future | 7.2 | 0.249914 | 0.274538 | 0.0246246 | 0.0198393 | 0.294378 |
| transform-full-0-1-7-training | 6.0 | 0.173118 | 0.195397 | 0.0222788 | 0.0189381 | 0.214335 |
| transform-full-0-1-7-future | 7.2 | 0.252445 | 0.277069 | 0.0246246 | 0.0198405 | 0.29691 |

Elapsed 250.88 seconds; charged 8/8 bounds and 102400/102,400 logical steps. Retained 70/256 allowed snapshots.

These are overlapping bounds on generated trajectories, not measured aircraft errors. The departure term is part of the position term; force is also included there. Do not add the table columns as independent contributions. No bound is reduced, no missing model comparison is completed, and no observational uncertainty or scientific detection is established.

[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
