# Stopping-consistency diagnostic implementation plan

**Approved bounded phase.** Native execution requires the source-bound software
qualification below; no nonlinear fitting is authorized.

**Goal:** explain the saved calibration stopping failure without changing the
solver, fitting parameters again or weakening acceptance checks.

**Architecture:** a shared fixed-point probe, a four-task study adapter and a
saved-evidence reporter. Reuse the frozen construction, error operator,
training protocol and stopping calculation through the existing `lll.studies`
lifecycle and trusted function-provider bindings. Copy no worker tree.

**Tech stack:** the existing pinned Python/NumPy/SciPy environment, unchanged
wide-precision native kernels, and CSV/JSON plus verified archive evidence.

**Spec:** [Public phase design](../PREDICTION_STOPPING_PLAN.md), based on the
[completed eight-record review](../prediction-phase-review/README.md).

## Global constraints and limits

- Preserve the original 209-file scientific freeze and its recorded environment;
  freeze new adapter/test sources separately before execution.
- Keep normalized bounds, all 26/27 columns, input geometry, noise law, initialization,
  fixed covariance anchor, clock and physical models unchanged.
- Preserve relative cost tolerance `1e-8`, stationarity `1e-4`, position RMS
  `0.001 m` and maximum position change `0.01 m`.
- Zero nonlinear fitting starts and zero new independent noise families. Any
  reconstruction of an exposed example must match the original array hashes.
- Four point tasks, 170 residual/tangent evaluations each. At most two compiler
  builds per worker, 59,954 prepaid native calls and 376,512,753 packet-query
  visits per task. Charge before execution; retain unused charges and failures.
- Software checks: 30 minutes; native diagnostics: two hours; reporting:
  30 minutes. Check deadlines cooperatively; finish an in-flight operation.
  Do not add tasks, retry completed identities or enlarge any allowance.
- Software checks use one thread. Native work uses two workers with one thread
  each and two reserved threads while the old suite remains active. Preserve
  this allocation even if more capacity becomes available.

## Exact saved selection

All identities are from `data/prediction-calibration-20261025` and use the
`increment` law and `sphere_rotating` model. Bind each fit's sealed SHA-256.

| Seed | Processing profile | Start | Role |
|---:|---:|---:|---|
| 281474976810725 | 0 | 0 | Successful preceding example |
| 281474976810726 | 0 | 0 | Failed start |
| 281474976810726 | 0 | 1 | Failed repeat |
| 281474976810726 | 1 | 0 | Successful processing control |

Read the saved normalized parameters; do not optimize or substitute another
point. This selection diagnoses a known failure and supports no population claim.

## Review focus

1. An active bound requires a feasible one-sided stencil, not a missing column.
2. Covariance/whitening must remain identical between residuals and derivatives.
3. Reconstructed inputs and parameter order must match the saved problem exactly.
4. Repeatability errors must be reported, not averaged away or relabeled convergence.
5. A diagnostic discrepancy is an outcome, not permission to change a threshold.

## Task 1: qualify the fixed-point probe

**Create:** `analysis/lll/stopping_consistency.py` and
`analysis/tests/test_stopping_consistency.py`.

**Interface:** `probe(evaluate, point, *, bounds, frozen_probe, reserve,
check_continue, maximum_evaluations=170) -> dict`. The evaluator returns a
residual and its complete Jacobian; the frozen probe supplies the original
actual-position stability calculation. The wrapper charges before every call.

- [ ] Write failing checks for bounds, complete columns, repeatability,
  derivative formulas and the finite evaluation counter.
- [ ] Implement three fresh base evaluations and steps `1e-3`, `1e-4`, `1e-5`
  in normalized coordinates. Use centered differences where feasible; otherwise
  use the second-order three-point one-sided stencil wholly inside the box.
  Evaluate every column at every step; retain timing-boundary effects explicitly.
- [ ] Invoke the unchanged undamped stopping probe once. The total is at most
  166 residual/tangent calls for 27 columns, within the 170-call ceiling.
  At most one bounded linear subproblem is solved per probe; no nonlinear fitter runs.
- [ ] Check twelve deterministic known-answer fixtures: six families at widths
  26 and 27—interior, lower-bound, upper-bound, near-dependent, exactly null and
  smooth nonlinear cases. Derive their reference minima and derivatives
  analytically, independently of the tested stopping code.
- [ ] For the smallest feasible step, compare derivative vectors using
  `error <= 1e-8 + 1e-6 * max(norm(reference), norm(difference))`.
  Preserve all three error curves. Whether the old stopping rule accepts a
  reference optimum is a reported finding, not a reason to alter the fixture.
- [ ] Add sixteen guards: changed source, changed environment, reordered or
  missing columns, invalid budget, overspend, missing or out-of-box point,
  invalid step, nonfinite output, repeatability discrepancy, replay discrepancy,
  infeasible stencil, accidental nonlinear-fit entry, protected seed and duplicate
  task charge. Reject invalid construction before native work.

**Verification:** run the two planned test modules through
`analysis/tests/run_numerical.py`, one worker/thread and two reserved threads.
Freeze the exact twelve fixtures and sixteen guards before their qualification
run. Diagnostic software must match the independent references before Task 2.

## Task 2: freeze and run the four native points

**Create:** `analysis/lll/stopping_consistency_study.py` and
`analysis/tests/test_stopping_consistency_study.py`.

**Interfaces:** `selection(root, prefix) -> list[dict]`,
`prepare(root, qualification) -> definition`, and `evaluate(task, context) -> dict`.

- [ ] Use `ClosedStudy` to bind the exact four saved fits, their original input
  recipe, array fingerprints, source bytes and environment. No protected or new
  calibration/validation seed may enter the definition.
- [ ] Reuse `ErrorTrainingFactory`, the generated-data construction and
  `generated_prediction.calculate`. Use `lll.studies.protocols.bind_function`
  on frozen `airquantumgrav_prediction.train_and_forecast` to replace only its
  `fit_training` provider with a capture/probe callback. End that protocol before
  nonlinear fitting or forecasting; do not monkey-patch modules or rewrite physics.
- [ ] Require exact reconstructed array hashes and parameter order, plus base
  cost replay within `1e-12 * max(1, abs(saved_cost))`. Preserve replay failures;
  do not change the saved point to make the match pass.
- [ ] Freeze four task identities, source/environment hashes, the finite budgets
  above and the qualified software evidence. Check completion and locks before
  launching once through the guarded `lll.studies` runner.
- [ ] Save repeated residual differences, every derivative column and step size,
  signed actual versus predicted cost changes, position changes and the original
  stopping-check components. Native discrepancies are diagnostic outcomes;
  preserve all four task outcomes rather than selecting favorable points.

## Task 3: audit, publish and end this phase

**Create:** `analysis/lll/stopping_consistency_report.py` and focused reporting
checks within `analysis/tests/test_stopping_consistency_study.py`.

**Interface:** `inspect(root, prefix) -> dict`, with CSV/Markdown rendering from
sealed records only. Reporting performs no native calls or fitting.

- [ ] Recheck hashes, source bindings, input replay, task/evaluation charges,
  all retained columns and absence of nonlinear-fitting calls.
- [ ] Report separately: repeatability, finite-difference consistency across
  scales, signed cost change, local-step conditioning and each stopping conjunct.
  Do not infer a new optimum or relabel either original failed fit.
- [ ] Publish an explanation, coordinate-level CSV and replayable evidence under
  `docs/prediction-stopping-consistency/`. Update the public roadmap and study
  index. Preserve inconclusive results and any unexecuted tasks explicitly.
- [ ] Stop for review after the report. A solver change, new noise campaign,
  validation run or new aircraft fit requires a subsequent reviewed phase.
