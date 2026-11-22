# Two-start generated method check

The faster tangent calculation **did not pass** its new two-start qualification
gate. All 12 paired tasks completed and passed their individual numerical and
physical checks. Across the six model/processing settings, only the two flat
settings passed the complete start-equivalence rule. The four globe settings
failed. This is a software-method result, not an Earth-model comparison.

The forecasts themselves agreed closely: the largest cross-method difference
among the selected starts was **1.75 × 10⁻⁹ m**, versus the predeclared 0.01 m
limit. The failed rule also required matched training costs to agree within
**1 × 10⁻⁸ relative**. Their largest relative difference was **1.18 × 10⁻⁵**
(an absolute difference of **6.18 × 10⁻¹⁷** in the study's cost units). In the
still-globe setting with profiled upstream removal, the two methods selected
different primary starts. Both selected forecasts were still within
**1.15 × 10⁻⁹ m**. These small absolute differences explain the failure; they
do not change its predeclared outcome.

| Physical setting | Removal profiled? | Gate result | Main reason |
|---|---|---|---|
| Globe with specified field | No | Fail | Training-cost tolerance |
| Globe with specified field | Yes | Fail | Training-cost tolerance |
| Globe with zero field | No | Fail | Training-cost tolerance |
| Globe with zero field | Yes | Fail | Training-cost tolerance and start choice |
| Stationary disc | No | Pass | All checks passed |
| Stationary disc | Yes | Pass | All checks passed |

The study used **240 of 4,824** permitted native calls and finished in about
**651 seconds**. Its sealed record verifies all 12 results, source and
environment bindings, and charge accounting. It used generated observations
only; no NASA or ESA recording or protected confirmation group was read. The
original observed exact-start failure remains unchanged, and the established
wide calculation remains the operational method.

The frozen rule compares near-minimum forecasts across methods. A future rule
must also bound forecast variation **within each method's** near-minimum starts
before it can establish start-choice stability. Any revised cost tolerance
needs independent numerical justification and a new prospective freeze; this
completed study cannot be rescored into a pass.

A separate, **post-study saved-result diagnostic** now checks that omitted
within-method spread. It passes three focused tests, including a case where
cross-method agreement hides a 0.02 m within-method difference. In this
finished study, every near-minimum set contains just one start, so the
within-method spread is zero in all six settings. This observation does not
repair the failed frozen training-cost and start-choice gates, nor does it
qualify the rule for settings with multiple near-minimum starts.

The [frozen plan](START_EQUIVALENCE_STUDY_PLAN.md) and
[method definition](START_EQUIVALENCE_METHOD.md) specify the tested question.
The packaged receipt and evidence are in the
[study record](start-equivalence-study/README.md).
