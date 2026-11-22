# Matched ESA weighting control implementation plan

**Goal:** Determine whether the newer code still produces an accurate
training-only forecast when it fits the same development recording with the
earlier receiver-only weighting.

**Architecture:** One separately frozen observed fit reuses the exact interval,
800 training receiver rows, 400 later query times, model, bounds, clock and
start from the completed six-fit study. It calls the current shared
`train_and_forecast` path with `training_error_factory=None`. A saved-only
report scores the forecast against the later receiver rows only after the
fit and forecast seal, then compares it with the earlier accurate pilot and
the sealed new IMU-error fit. No reserved confirmation group is an input.

**Files:** `analysis/lll/esa_weighting_control_study.py` owns the one-task
definition and evaluator; `analysis/lll/esa_weighting_control_report.py`
owns the saved-only comparison; focused tests live in
`analysis/tests/test_esa_weighting_control_study.py` and
`analysis/tests/test_esa_weighting_control_report.py`. The result and next
gate belong in this directory and the public roadmap/index.

## Frozen scientific choices

- The source is the prepared ESA recording-187 interval with 360,028
  increments and 1,200 receiver times. The first 800 receiver rows train;
  the last 400 are withheld until the forecast seals.
- Use the original linear-point increments, `sphere_rotating`, no upstream
  removal, `reported-short-v1`, start zero, packet-header elapsed clock,
  inverse-square height gravity, the same 26 bounds and a 200-evaluation cap.
- Use the receiver-only dense working covariance. This is an observed-data
  development control, not a calibrated choice between error laws.
- One task, one worker, one numerical thread, one start, no retry. Freeze a
  finite 201-native-call, 45-billion-visit ceiling and a four-hour
  cooperative wall allowance before launch. Preserve charges and any failure.
- The task is a **technical pass** only when the fit and forecast are complete
  and numerical checks pass. Physical accuracy is scored separately against
  the preset 10 m horizontal training and later RMS screen. Neither outcome
  promotes a scientific decision.

## Implementation steps

- [ ] Add tests that reject unqualified preparation, changed source/input
  bindings, any later receiver row in the worker, and a missing sealed
  comparator. Run them and confirm failure before implementation.
- [ ] Implement the one-task study using `lll.studies`, the existing
  `esa_fixed_rate_protocol.material`, and shared training/forecast functions.
  Reuse the sealed six-fit study's input bytes; do not copy its worker.
- [ ] Qualify the source-bound worker and interruption recovery. Freeze its
  inputs, environment, allocation and finite charges, then run once.
- [ ] Build a saved-only report that verifies the closed task and both
  historical comparators before reading the later receiver rows. Report fit
  status, physical errors, parameter differences and absolute adequacy.
- [ ] Update the public roadmap, study index and overview with the verified
  result and the next gate. Preserve all prior results unchanged.

The seven reserved ESA flight groups stay closed. A failed fit or accuracy
screen is a result to report, not a reason to alter bounds, timing, noise
levels or allowances.
