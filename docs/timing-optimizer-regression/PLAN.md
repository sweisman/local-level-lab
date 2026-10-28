# Native qualification of timing-aware stopping

## Question

Does the [analytically qualified method](timing-stopping-qualification/INTERPRETATION.md)
also work through the complete generated-input fitting and prediction path,
with the original physical integrator, error model and calibration bounds?

## First gate: four regression cases

Use only the already exposed seeds 281474977010692 and 281474977010693,
point-observation input law, specified-field globe, profiled processing
parameter and original starts 0 and 1. These are the two passing controls and
two numerical failures preserved in the closed calibration record.

Regenerate their original inputs and run one new fit from each original
declared start. Verify exact input-array, training-observation and error-operator
bindings against the saved records. Do not start from the old fitted answers,
select a preferred start using forecast errors or change either noise draw.

Use explicit provider hooks through the shared structured-input runner,
training protocol and counted fitting adapter. Select the new timing-aware
solver only for this frozen study. Preserve the default providers and archived
source; do not copy a worker or patch process-global functions.

Keep all 27 active parameters, compensated mean calculation, noise propagation,
physical bounds and existing numerical/forecast limits. Record every final
timing cell, actual cost/position check and original label. Predictions from
both starts must meet the predeclared agreement checks, including physical
height. Numerical completion alone is insufficient.

## Finite allowance

Four fits, at most 200 fit evaluations each, no retries. The 36-evaluation
timing-verification reserve and two near-zero repeats are included in that
200, not added to it. Retain the existing mean forecast and error-propagation
diagnostic, including their unchanged operation accounting.
Derive construction/native call/packet limits from the unchanged shared recipe
before preparation, and freeze their exact totals.

Use four workers with one numerical thread each, at most two kernel builds per
worker and a one-hour cooperative ceiling. Expected runtime is about 5–20
minutes. Separately precharge at most 620 bounded linear operations per fit,
100 iterations each. Freeze source, environment, identities, selection,
allowances and software qualification before launch. Preserve every failure
and close all unused work at termination.

## Broader gate and interpretation

Only if all four regression fits, replay checks and required start comparisons
pass, prepare a separate replication of the earlier 48-case optimizer
qualification: its same exposed development seeds, two input laws, all three
candidates, both processing settings and two starts. Retain its 200-evaluation
per-fit limit and derive a new finite source-bound allowance; do not reuse its
closed budget. Freeze that phase separately before execution.

A failed gate blocks its dependent phase. Neither stage reopens a calibration
campaign, estimates a threshold or uses protected aircraft observations. Native
optimizer qualification is a prerequisite for proposing another calibration
release, not permission to restart one automatically.

[Next analyses](NEXT_STEPS.md) · [Technical roadmap](ANALYSIS_ROADMAP.md).
