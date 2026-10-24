# Complete short noisy protocol

**All 128 software checks pass**, including twelve complete native fitting and
forecast paths. These cover all three generating models, both processing
assumptions and both input-noise formats.

Each two-second example has only six earlier receiver positions and allows
eight fitting evaluations. All twelve raw and error-conditioned forecasts
meet the physical error screen, but **none passes the numerical stopping
checks, and none uniquely identifies the later prediction through unrestricted
calibration**. Those outcomes are preserved. This is an interface qualification,
not successful long-duration prediction validation.

The calculation now distinguishes two questions: predicting another receiver
reading includes receiver errors; predicting the aircraft's physical position
does not. The checks preserve identical training covariance, remove only future
receiver contributions for the physical target, and save both forecasts before
opening later truth. Withheld positions never choose weights or corrections.

The [receipt](evidence-receipt.json) verifies 146 artifacts, including 137 source
snapshots, native compilation, twelve charged starts and all work. The test
attempts 11,352 native calls and 108,612 normal variates; it reads no aircraft
or protected confirmation measurements.

The [shared evaluator and saved-results auditor](../shared-native-protocol-qualification/README.md)
also pass the same 128-check matrix; this is software verification, not an
additional set of physical observations.

Next is a separately frozen, longer noisy fitting study with more training
positions and the existing numerical and physical acceptance checks. The
original failed twenty-minute noisy study and 53-stretch findings are unchanged.

[Frozen short-case plan](../NATIVE_PROTOCOL_PLAN.md) ·
[Nonlinear validation plan](../NONLINEAR_PLAN.md) · [Next analyses](../../NEXT_STEPS.md).
