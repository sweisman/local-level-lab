# Checking the next timing boundary

Five selected flight stretches remain unresolved. The [saved-result diagnosis and
finite plan](PLAN.md) separates their different numerical problems.

The first observed target is one primary/repeat pair whose stationarity and
movement checks passed, but whose correction reached an unchecked neighboring
timing boundary. The new wrapper checks that boundary with the original
two-sided rule. It does not weaken the rule or change the physical model.

The scope is two existing smooth controls and that one target pair: four
identities, at most 66 native evaluations, four numerical threads and no retries.
Every required companion and repeat comparison remains necessary before the
stretch's disposition can change. The other four unfinished stretches are
outside this numerical trial.

The [separately frozen software controls](../ilvis0-boundary-followup-controls-v3-20261016/README.md)
passed 65/65 before launch. The worker is
`analysis/tests/ilvis0_boundary_followup_worker.py`; `--package-only` publishes
completed evidence without performing fits. Earlier results remain preserved.

[Current findings](../CURRENT_STATUS.md) · [All 53 stretches](../ilvis0-current-findings-20261015/STRETCHES.md) ·
[Next steps](../NEXT_STEPS.md).
