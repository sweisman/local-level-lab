# Completed protocol comparison — 2026-10-06

All **72 geometry-only evaluations** completed with **zero fit failures** and all fits
converged. Charged evaluation time was **516.91 seconds (8m37s)**, within the 15-minute cap,
using two numerical threads. Neither protocol passed every required comparison. This is
development screening, with zero bootstrap and no calibrated model decisions.

An **IMU (inertial measurement unit)** measures motion. This comparison tests whether flight
directions and deliberate IMU turns leave enough independent information to distinguish the
three Earth models after allowing for aircraft motion and IMU error. The crab fit describes
how wind can make the aircraft point away from its direction of travel; both a flexible
dynamic fit and an explicit wind fit were tested.

## Protocols and results

The original nominal 75-minute protocol was compared with a nominal 90-minute protocol:
headings 10°, 190°, 100°, 280°, 10°, 190°, each for 15 minutes, with IMU turns at minutes
5, 20, 35, 50, 65 and 80. The simulator adds ten minutes of flight slack, so nominal protocol
duration is not the full recording or qualifying cruise duration.

Each arm has 36 cases: three model truths, mixed-bias and wind scenarios, two crab fits, and
three fresh paired development seeds, 600501–600503. Arms were interleaved within each seed.

| Protocol / crab fit | All design comparisons informative | Passed scientific screen | Model-test ranks |
|---|---:|---:|---|
| Original / dynamic | 18/18 | 18/18 | 18 rank 2 |
| Original / wind | 9/18 | 6/18 | 15 rank 2, 3 rank 1 |
| Revised / dynamic | 0/18 | 0/18 | 18 rank 2 |
| Revised / wind | 0/18 | 0/18 | 12 rank 2, 6 rank 1 |

Rank counts the independent combinations of model signals retained by the numerical test.
Rank alone is insufficient: each intended comparison must retain enough information, and
the rank must be stable near the cutoff. Instability excluded six original/wind, thirteen
revised/dynamic and ten revised/wind cases; these exclusions overlap information failures.
Worst design margins were -0.311505 for the original and -0.307931 for the revised protocol.

All returned model decisions abstained. Passing this development screen does not establish
robustness to prior assumptions, calibrated power or a false-rejection bound. Protective
gates and the original science cutoff were retained; unfavorable cases were not rerun.

## What the comparison revealed

The revised protocol passed simplified tangent calculations with known IMU axes. It failed
when the complete simulator and recording-processing chain reconstructed those axes.
Its IMU turn at minute 20 also overlaps the first simulated aircraft turn. The causal effect
of that overlap has not been isolated; it cannot yet explain the failures by itself.

The preceding saved-record audit corrected numerical nuisance-rank dependence on parameter
units by normalizing nuisance columns. It also identified short qualifying legs, slow signals
absorbed by changing IMU bias, and sensitivity near a rank cutoff. Historical results retain
their original source and environment freezes.

Next use saved processing diagnostics and independently checked trajectory/attitude fixtures
to separate timing and IMU-axis reconstruction from limits imposed by the nuisance models.
The old calibration proposal is stale after the numerical change and thread switch. Final
domain review and a new freeze must precede fresh calibration. Real IMU bench testing and
observed-track replay remain pending.

## Technical record and recovery

Worker: [geometry_campaign.py](../../analysis/tests/geometry_campaign.py). The documented corpus
contains `manifest.json`, `records.jsonl`, `records.jsonl.gz`, `budget.json`, `status.json`,
`summary.json`, `review.json`, `launch.json`, `worker.log`, `run.lock`, `case-input.json`,
`case-output.json`, and `recovery.jsonl` only if needed. The comparison input and audit are
preserved in the [preceding geometry study](../geometry-development-20261006/README.md).

The completed review verifies source/environment/runner/input freezes, exact task identities,
lossless compressed journal and recomputed scores. The worker preserves failures, fsyncs
records, enforces a single-worker lock and charges interrupted reservations conservatively.
Each protocol score requires all 36 expected cases.

**Do not launch or resume this completed campaign.** Its 72-case authorization is exhausted;
remaining time does not permit extra cases. Historical launch PID 3564298 is not an active
worker. Original launch used the worker's `--output docs/protocol-development-20261006`,
`--protocol-plan docs/geometry-development-20261006/protocol-comparison-plan.json`,
`--wall-time-minutes 15 --detach` options and numerical thread settings of two. Recovery
instructions apply only to an interrupted campaign under an unchanged freeze, never to
restarting completed cases. Further flights, calibration and git operations require consent.
