# Three-pair method check: wall-cap audit

**The revised method is not qualified.** All three paired tasks
reached the frozen four-hour wall cap before a paired comparison
was saved. The run charged 349 native calls and sealed every task
as a budget failure. No task remains unfinished, so the prepared
unfinished-task recovery route does not apply.

Two saved wide fits passed their numerical stopping checks; one did not.
That partial result cannot qualify the revised method.

| Development case | Charged calls | Wide stopping check | Revised fit and forecast |
|---|---:|---|---|
| flat_still-0-reported-persistent-v1-0 | 127 | pass (72 evaluations) | Not completed |
| flat_still-0-reported-short-v1-1 | 108 | pass (94 evaluations) | Not completed |
| flat_still-1-reported-short-v1-0 | 114 | fail (88 evaluations) | Not completed |

The saved wide-method artifacts are partial task evidence.
They do not make any paired result pass. The established wide
method remains the qualified implementation for this development
analysis. This method check makes no Earth-model decision.

[Verified paired-result table](README.md) · [Frozen plan](../../mixed-tangent-hybrid/V2_PAIRED_PLAN.md)
