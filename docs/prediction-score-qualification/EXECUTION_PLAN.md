# Independent prediction calibration: execution design

## Population and decision

Reuse the completed pilot's generated population: 120 seconds at 300 Hz,
119 receiver queries, 79 earlier training queries, latitude +55°, fast turning
and climbing, inverse-square height gravity, both input-error laws, three
generating/fitted models, both processing cases and two starts. Reuse the
fixed positive/negative calibration fixtures in
`lll.airquantumgrav_observation_truth._parameters`; estimate their corrections
from training observations, without supplying truth to the estimator.

This tests the nonlinear fitting procedure under declared errors. It does not
cover every calibration value inside the allowed bounds or establish aircraft
noise characteristics. Original observations and reserved ESA groups are absent.

Bind one population SHA-256 to the common recipe, every numerical source and
the exact environment. Role and seed lists are separate frozen inputs. Reuse
`structured_noisy_study.run_case`, `independent_noisy_study.score_records`,
the shared primary selector and `prediction_calibration` rather than copying
the worker or navigation calculations.

## Fixed phases

| Phase | Independent seeds | Seed interval, inclusive | Fits | Cooperative ceiling |
|---|---:|---|---:|---:|
| Calibration | 299 | `281474976810656`–`281474976810954` | 7,176 | 120 hours |
| Validation | 181 | `281474976910656`–`281474976910836` | 4,344 | 72 hours |

Each phase uses two workers with one numerical thread each. Reserve the two
threads held by the existing suite until it releases them. Preserve 200 fit
evaluations per start, no retries, 59,954 prepaid native calls and 376,512,753
packet-query visits per start. These are separate allowances, not extensions
of the completed pilot. Expected combined time is about 175 hours with two
workers; the ceilings are execution limits, not expected runtimes.

The calibration limit is its maximum seed-family score: 99% population content
at 95% confidence requires rank 299 of 299. Validation tests 95% coverage at
95% confidence, allowing four failures in 181 independent seed families.
Both the threshold and validation target must be frozen before validation
starts. All earlier pilot, software-qualification and legacy seeds are excluded.

## Fail-closed handoff and early futility

Do not launch validation unless the closed calibration cohort supplies a finite,
hash-verified threshold under the same population. Never choose a threshold
using validation outcomes, or drop an unavailable seed family.

Calibration can stop cooperatively once a setting has no numerically qualified
start: that seed's infinite score makes the maximum-order-statistic threshold
unavailable regardless of unexecuted draws. One failed start alone is insufficient.
Validation can stop after five distinct seed families definitely fail; later
draws cannot restore the predeclared acceptance criterion. Use the existing
manifest-bound stop request, never a process signal. Preserve in-flight charges
and every failure. Record completed work separately from planned work; do not
calculate binomial bounds from unexecuted draws in either early-stop branch.

## Shared implementation and qualification

- Add `lll.prediction_calibration_study`: `population(sources, environment)`,
  `recipe(role)`, `case_recipe(seed)`, `tasks(role, population_sha256)`,
  `evaluate(task, context)` and `prepare(...)`. Validate the population, source,
  environment, role and task identity before any draw, build or charge.
- Add `lll.prediction_family_state` for immutable per-case selection markers
  and the cooperative futility check. Markers bind the manifest, seed, setting,
  start, numerical completion, training cost and complete-block score. Start
  selection uses training cost only. Reporting rechecks markers against sealed
  outcomes; markers alone cannot establish a scientific result.
- Add `lll.prediction_calibration_report` for closed per-case replay through
  the existing auditor, independent-family aggregation, calibration artifact,
  validation handoff and separate counts of numerical/physical failures.
- Qualify these interfaces with at most 32 new deterministic metadata cases
  plus the 30 ledger regressions, one thread with two reserved, two minutes per
  test group, zero new fits or random draws. Reverify the existing source-bound
  native qualification and completed pilot dependencies; do not rerun those
  studies. Reject a changed scientific dependency instead of assuming compatibility.
- Freeze both source/environment and the finite phase definition after software
  qualification. Verify locks and completion before the calibration launch.
  A failed qualification blocks execution. Preserve all protected data and
  existing result labels regardless of this study's outcome.

[Calibration method](CALIBRATION_PLAN.md) · [Target separation](CALIBRATION_TARGETS_PLAN.md) ·
[Sample-size calculations](CAMPAIGN_SIZING.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
