# Full matrix check of the corrected optimizer

**Question:** does the corrected bounded linear calculation work across both
input formats, all three generating models and both processing settings?
The [six-case regression](timing-feasible-native-regression/INTERPRETATION.md)
passes, including the latest calibration failure at its unchanged fitted cost.
This broader test must pass before another calibration release is considered.

## Inputs and method

Reuse the 48 exposed development cases from the
[original matrix](compensated-optimizer-qualification/INTERPRETATION.md): seeds
281474976810725 and 281474976810726; point-rate and increment inputs; the
specified-field globe, zero-field globe and stationary disc; two processing
settings; and the same two declared starts. Each candidate fits its own generated
truth. These are software controls, not 48 new model votes.

Keep the original observations, error law, physical bounds, starting points,
all 26 or 27 nuisance columns and every acceptance limit. Preserve four exact
original input/training/error-operator replays and the original failure labels.
The corrected calculation starts each bounded linear solve at its feasible
zero-step anchor and rejects worsening answers. No scientific threshold changes.

The prerequisite is the independently audited six-fit publication, bound by
manifest `f2c63e792616bcaf9909a61da562339314935f552f3d1df73fbf7395e41bbd6b`
and summary `b9031118b5a3d5fef32e6907e33dcc339c4f15698dead97bacddbad9aaa02adf`.
All seven numerical source hashes and the runtime environment must match.
Only the documented reporting repair differs from that execution freeze.
Use the shared study worker, counted solver and independent saved-result auditor;
the new module contains only this study's policy and metadata.

## Finite allowance

Freeze sources, environment, task table, selection and software qualification
before execution. Use four workers with one numerical thread each. The ceiling
is 48 starts, 200 evaluations and 620 bounded linear operations per start,
100 iterations per operation, with no retries. Maximum native prepayments are
2,877,792 calls and 18,072,612,144 packet visits. The cooperative wall ceiling is
two hours; the preceding matrix took about 66 minutes. Charge before work and
close all unused allowance at completion. No closed study is resumed.

## Acceptance and next step

Require all 48 numerical and physical forecast checks, all 24 paired-start
comparisons, and all four original replays to pass. Keep the existing training
cost/position repeat limits and the separate later horizontal/height accuracy
screens. Publish every result, including failures, without refitting during audit.

A pass qualifies this generated-data matrix. It does not establish calibrated
prediction intervals or confidence for aircraft results. Any new calibration
requires disjoint cohorts and a separately reviewed finite allowance; all previous
calibration allowances stay closed. The original 53 aircraft results and protected
ESA confirmation groups remain unchanged.

[Next analyses](NEXT_STEPS.md) · [Study index](STUDIES.md).
