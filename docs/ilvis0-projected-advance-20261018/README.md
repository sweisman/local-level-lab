# Qualification pipeline

This sequence checks the fitting software before it changes any recorded-flight
analysis. Every numerical stage has its own finite allowance and preserves
earlier failures. The background coordinators do no numerical fitting.

**Completed without advancement.** Both continued fits passed individually,
but their paired objective comparison still failed. The complete saved review
retains eleven of twelve passing pairs; the dependent broader full-calibration
matrix did not start. This coordinator is finished, not waiting.

The separate [horizontal-only capability](../ilvis0-projected-horizontal-review-20261018/README.md)
passes every horizontal case. Its [full-calibration controls](../ilvis0-projected-horizontal-fullcal-20261018/PLAN.md)
form a new, explicitly narrower software study. Height-only remains unqualified.

| Stage | Purpose and gate |
|---|---|
| [Complete local-probe matrix](../ilvis0-projected-local-qualification-20261018/README.md) | All 24 generated fits pass individually; eleven of twelve paired-start checks pass. The remaining pair blocks advancement. |
| [Saved-endpoint continuation](../ilvis0-projected-budget-continuation-20261018/PLAN.md) | Gives both endpoints a separately frozen larger budget while retaining the same numerical limits. Two starts; at most 1,204 native calculations. |
| Complete saved-result review | If the continued pair passes, combines those two results with 22 unchanged companions and verifies all twelve paired comparisons. This performs no new fitting. |
| [Full-calibration controls](../ilvis0-projected-fullcal-qualification-20261018/PLAN.md) | Starts only after the complete review passes. Tests all 26/27 nuisance columns under both processing cases: 24 generated fits, at most 3,888 native calculations. |

The remaining pair's predictions differ by no more than about 1.3 micrometres,
but their objective difference exceeds the frozen repeatability limit. That
limit remains unchanged. The continuation is intended to distinguish an
insufficient numerical budget from an unresolved optimizer problem.

The coordinator checks completion hashes, publication and released worker locks
before each handoff. A failed gate stops dependent numerical work. Previously
failed qualifications remain failed; the review is a separately identified result.

These are generated-motion software controls. They read no original recordings
and start no observed-data fits. They do not alter the existing **53 globe /
0 flat / 0 unresolved** comparison. A passing full-calibration stage permits
preparation of a small matched recorded-data study, not an automatic archive rollout.

[Next analyses](../NEXT_STEPS.md) · [Measurement contributions](../ilvis0-measurement-contribution/README.md).
