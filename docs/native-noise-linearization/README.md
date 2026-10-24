# Propagating measurement errors through the flight calculation

**All 182 source-bound software checks pass.** These include 65 native adapter
checks and regressions for covariance, receiver errors, linear calibration
uncertainty and work accounting, plus two test-portability checks. They use
generated data, not new flight fits.

The calculation now supports both input types: recorded increments, as in the
Applanix archive, and increments converted from rate samples, as in the ESA
study. Neighboring rate intervals retain their shared endpoint error.

Twenty-four 600-packet cases cover both input laws, all three candidates, both
processing assumptions and both gravity treatments. Their nominal positions
match the original wider calculation exactly after the same output conversion.
Twenty-four short cases agree with independent nonlinear noise perturbations;
the largest normalized covariance discrepancy is about 1.1 parts per million.

Two larger receiver checks retain all 33 required error states. Earlier-only
predictions and every active calibration column agree with independent dense
calculations. Twelve earlier incremental-input comparisons also pass unchanged.

The run uses **23,984 native calls, 39,594 packet steps and two builds** in
35.5 seconds. Complete case allowances are charged before execution; interrupted
cases keep their charge and cannot retry. The audit verifies all 63 charged
identities, actual attempts, compiler/source/binary bindings and
[77 artifact hashes](point-native-ci-qualification/evidence-receipt.json).
The earlier [180-check snapshot](point-native-qualification/evidence-receipt.json)
is preserved. The portability revision changes one test file and adds one
archive object; numerical library sources and work allowances are unchanged.
Ordinary tests need no local qualification files. Formal runs retain their
mandatory source/environment gate.

## Earlier gates

| Check | Result | Preserved evidence |
|---|---|---|
| Single-step derivatives | 18 checks; all fifteen state/input directions agree with independent perturbations | [Receipt](qualification/evidence-receipt.json) |
| Initial complete-history path | 38 checks; nominal positions and accumulated covariance agree | [Receipt](history-qualification/evidence-receipt.json) |
| Initial receiver combination | Twelve cases; native means, covariance and calibration columns agree | [Receipt](combined-qualification/evidence-receipt.json) |

## Next gate

The calculation above holds calibration fixed. A separate
[linear calibration component](../integrated-noise-covariance/CALIBRATION_PLAN.md)
passes 15 checks and returns no finite prediction covariance when unknown
parameters can change the forecast.

The [training-only fitting adapter](../integrated-noise-covariance/training-adapter-qualification/README.md)
now passes 56 checks. Next qualify parameters at bounds and nonlinear prediction
coverage. The actual archive
error law still needs assessment. No original or protected data were read,
and the completed 53-stretch findings are unchanged.

[Current adapter plan](POINT_NATIVE_PLAN.md) · [Rate-point law](../integrated-noise-covariance/POINT_PLAN.md) ·
[Earlier history plan](HISTORY_PLAN.md) · [Single-step plan](PLAN.md) ·
[Receiver combination](COMBINED_PLAN.md) ·
[Covariance component](../integrated-noise-covariance/README.md) ·
[Completed noise test](../esa-noisy-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
