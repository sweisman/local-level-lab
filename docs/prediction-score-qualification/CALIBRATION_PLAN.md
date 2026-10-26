# Calibrating prediction errors across independent draws

## Purpose

Test the complete fitting procedure, including uncertainty caused by estimating
calibration. Keep the existing complete-block error score, calibration limits
and training-only choice of start. Do not infer a threshold from the two
completed pilot seeds.

The first deliverable is bookkeeping and sample-size software, not another
fitting campaign. New draws require a separate frozen population, source and
environment, seed list, selection rule and finite execution allowance.

## Independent unit and scope

One seed generates a family of related settings. Retain both input-error laws,
all generating/fitted models, both processing cases and both starts. Choose a
start for each setting by qualified training cost, then declared start order.
The seed's score is the maximum over its selected settings and their complete
later position blocks. Settings sharing a seed are not independent trials.

A missing or numerically unavailable setting makes that seed unavailable.
Never drop such a seed from calibration or validation. Treat it as an infinite
score when selecting an order statistic, and as a failure when testing a finite
threshold. Position-error screens remain separate; they must not select draws.

Pilot, calibration and validation seeds must be disjoint. Bind every draw to
the same population hash: generating geometry and calibration, measurement-error
law, procedure, source and environment. A result for one generated population
does not cover untested calibration values, durations or actual aircraft errors.

## Statistical calculation

For independent identically distributed nonnegative scores, an upper tolerance
limit can be an ordered calibration score. For coverage `c`, confidence `g`,
`n` calibration draws and ascending one-based rank `k`, require
`P(Binomial(n, c) <= k - 1) >= g`. Choose the smallest supported rank. If none
exists, return unavailable; never extrapolate a finite threshold.

This is a one-sided order-statistic construction. It does not assume normally
distributed scores. Ties are conservative when validation counts scores strictly
above the threshold. The independent-draw assumption and frozen population are
essential. The [NIST tolerance-interval guide](https://www.itl.nist.gov/div898/handbook/prc/section2/prc264.htm)
explains the distribution-free approach and its sample-size cost.

Validation uses all preassigned independent draws, including unavailable ones.
Reuse the existing exact one-sided binomial upper bound and sample-size
functions in `lll.research_calibration`; reuse no passenger-study threshold,
selection policy or device assumption. A validation bound is a statement about
this generated prediction procedure, not Earth-model significance.

## Implementation and qualification

- [ ] Add `analysis/lll/prediction_calibration.py`. Expose
  `aggregate_draws(rows, tasks, *, role, population_sha256, excluded_seeds)`,
  `order_statistic_plan(draws, *, coverage, confidence)`,
  `calibrate(draws, *, coverage, confidence, population_sha256, excluded_seeds)`
  and `validate(calibration, draws, *, confidence, population_sha256)`.
- [ ] In `analysis/tests/test_prediction_calibration.py`, check shared-seed
  dependence, training-only selection, every missing/failed setting, duplicate
  or reused seeds, altered roles/populations and nonfinite scores. Show that
  accurate but numerically unavailable starts cannot select themselves.
- [ ] Check order-statistic probabilities by independent small binomial sums.
  At 95% coverage and confidence, 58 draws cannot supply a finite limit; 59
  can use their maximum. Check strict exceedance and exact binomial validation
  against the closed-form zero-failure result. These are test examples, not
  a preregistered scientific confidence target.
- [ ] Run at most 32 deterministic checks with one numerical thread and two
  reserved for the existing suite; zero random draws, native calls and fits.
  Record source-bound evidence before any execution definition consumes them.
- [ ] Compute campaign sizes and runtime from independent seed families,
  including allowed failures and power. Freeze the actual nuisance population,
  confidence targets, disjoint draw identities and finite compute limits before
  launching. Do not mistake a simulation-population result for uniform coverage
  over every allowed calibration parameter.

The current aircraft findings and all earlier failed gates remain unchanged.

[Completed pilot](../independent-noisy-training-pilot/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
