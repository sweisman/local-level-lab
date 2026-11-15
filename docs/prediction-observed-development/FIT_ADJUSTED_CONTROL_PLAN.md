# Fit-adjusted error-scale control implementation plan

> **For agentic workers:** Implement this plan in the current workspace using
> the shared study library. Do not delegate, commit or push without the
> separately required user instruction.

**Goal:** Check whether full nonlinear fitting under the two *supplied* error
laws can itself produce a training cost as small as the ESA value of 7.15.

**Architecture:** Generate two independent known-answer aircraft recordings at
the ESA development cadence. Fit both declared IMU error laws to each same
recording using the existing native training path. Compare the saved whitened
costs and complete local Jacobians with the same saved-only calculation used
for the ESA recording. This is a software diagnostic, not aircraft calibration.

**Tech stack:** Python, NumPy, existing `lll.studies` lifecycle, shared native
aircraft model, `analysis/tests/run_numerical.py`.

**Spec:** [Prediction-error requirements](../PREDICTION_ERROR_LAW_PLAN.md) and
the [observed local-fit result](TRAINING_LINEAR_REFERENCE.md).

## Fixed scope and limits

- Two generated truths: one recorded-increment input-error draw and one sampled
  rate-point draw, with distinct predeclared seeds `20261115001` and
  `20261115002`. Each truth receives both candidate-law fits on identical
  generated IMU and receiver measurements: **four fits total**.
- Use the existing independent sensor-error generator and aircraft truth
  components. Set one 900-second, 300 Hz flight at 55° latitude, 900 one-second
  receiver reports, the first 600 for fitting, the generator's climb height
  profile, interior calibration, and the specified-field globe as generated
  truth. Generate receiver errors with an independent random stream.

**Ruling:** The shared 900-second generator supports its declared climb height
profile, not a level-height profile. Use that known-answer path for this
software control. The cost is that this two-case result cannot be called a
level-flight calibration.
- Save both 26-column fitted Jacobians, whitened residuals, all numerical
  failures, source and environment hashes, charged work and complete seed
  identity. No NASA or ESA observed values or protected flight groups enter
  generation or fitting. The ESA result is read only during final comparison.
- Maximum **200 fit evaluations per candidate**, two workers of one numerical
  thread each, at most **1.4 million native calls and 90 billion packet visits
  per generated recording**, and a **two-hour** study wall cap. Charge work
  before execution. Preserve a failed/unfinished result at the cap; do not
  extend the active allowance. These are ceilings, not expected usage.
- Before launching, run a short frozen-worker preflight and a reboot recovery
  test proving sealed tasks are reused and only unfinished work is scheduled.
  The resume command must verify source, inputs, environment, leases and charges.

## Tasks

### 1. Generated input and matching check

**Files:** Add `analysis/lll/esa_fit_adjusted_control_study.py` and
`analysis/tests/test_esa_fit_adjusted_control_study.py`.

- [ ] Test that the two seeds generate distinct truth, while both fits within
  one task receive byte-identical IMU increments and receiver reports.
- [ ] Test the exact 900/600 split, true model, timing, source bindings and
  rejection of changed tasks before any observation or native call is read.
- [ ] Reuse the existing generator and native fit components; store raw
  generated increments and reports along with the input hashes.
- [ ] Run the focused tests with `/home/sweisman/venv/bin/python -m pytest -q`.

### 2. Finite lifecycle and recovery

**Files:** Add `analysis/lll/esa_fit_adjusted_control_recovery.py` and focused
tests in `analysis/tests/test_esa_fit_adjusted_control_recovery.py`.

- [ ] Freeze the exact tasks, seeds, source closure, numerical environment,
  per-task charges, two-thread allocation and two-hour cap through
  `lll.studies`.
- [ ] Test interruption before result sealing, rejection of source/input
  mutation, and reuse of a sealed failure as well as a sealed success.
- [ ] Pass source-bound tests and one short frozen-worker preflight before the
  two-recording run. Save the qualification receipt and idempotent resume
  command.

### 3. Saved-only comparison

**Files:** Add `analysis/lll/esa_fit_adjusted_control_report.py`, its focused
test and `docs/prediction-observed-development/FIT_ADJUSTED_CONTROL_RESULT.md`.

- [ ] Verify every fit artifact and charge through the sealed study, then use
  `esa_training_linearization_report.analyze_fit` on each passing fit.
- [ ] Report all four outcomes, local ranks, costs, cost-to-linear-reference
  ratios, and the unchanged ESA value. Keep failed fits in the denominator.
- [ ] Report whether this **two-case diagnostic** reproduces a similarly tiny
  training cost. Do not calculate a tail probability or claim a calibrated
  rejection from two generated recordings.
- [ ] Update the study index, roadmap and next-steps page with the verified
  result and next gate. Any larger calibration cohort gets a separate frozen
  sample-size and compute allowance.

## Review focus

The tests must also cover nonfinite generator output, a receiver report whose
timestamp falls outside the generated IMU support, differing two-law input
hashes, a bound-active or numerically unfinished fit, and a completed task
that cannot be rerun after reboot.
