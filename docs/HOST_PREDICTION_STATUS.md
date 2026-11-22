# Prediction calibration and independent validation

**Generated-data calibration and combined validation passed their frozen rules.**
Calibration verified all 7,176 forecasts across 299 seed families and fixed a
threshold of 27.6605 on the predefined normalized forecast-error score. The
independently replayed [combined validation](prediction-validation-continuation/README.md)
verifies all 4,344 prescribed fits across 181 separate simulated cases. None
exceeded the fixed threshold or was unavailable. The one-sided 95% failure
upper bound is 1.64%, below the declared 5% target.

These results validate the procedure under its **generated-data assumptions**.
They do not establish error coverage on real aircraft or Earth-model
significance. [Read the calibration result in plain language](prediction-calibration-host-20261030/INTERPRETATION.md).

## How the interrupted run was completed

The original validation run stopped after a host reboot. Its 3,750 completed
fits remain saved and passed; four starts were charged but unfinished and 590
were never started. Its own frozen rule required every charged start to finish,
so that original run remains classified as interrupted. Of its 181 cases, 155
had all 24 fits complete. The calibrated threshold remained fixed.

The [separate continuation](VALIDATION_CONTINUATION.md) completed all 594
remaining fits. Its first technical release stopped after 93 charged software
errors caused by a deadline adapter mismatch; that stage remains sealed. The
corrected release passed all 594 fits with zero errors. Its service was disabled
and removed after verified closure. The original 3,750 completed fits remain
unchanged, and the original interrupted run is still classified as interrupted.

The [prelaunch snapshot](host-calibration-preparation/README.md) passes all 154
software checks. The 7,176-start source/input freeze and numerical environment
match the verified launch. Independent validation began after verified archiving
and its own preparation checks.

The previous campaign remains closed: 1,813 completed simulated fits passed,
four starts were interrupted and no uncertainty threshold was established.
These are generated-data checks, not additional aircraft findings.

## What has passed

- The original 48-case optimizer qualification, all 24 starting-point pairs and
  four original-input replays.
- The recovery checker and a host-service test that continued after its
  submitting command exited, then completed all eight heartbeats.
- The interruption-reporting repair and fresh release guards. All 154 checks
  pass against 260 source files and the numerical environment. The one reporting
  update has explicit old/new hashes; other qualified numerical sources match.

The original frozen validation policy required an uninterrupted cohort, so its
rebooted run remains interrupted. The separate continuation uses qualified
task-level recovery with finite charges. Completed unsuccessful fits keep their
original selection and failure rules; a technical interruption can be retried
only under the new release's recorded recovery allowance. The scientific
acceptance limit is unchanged.

## Approved finite compute

| Phase | Maximum fit starts | Estimated duration at four threads | Wall ceiling |
|---|---:|---:|---:|
| Calibration | 7,176 | About 6.4 days | 10 days |
| Independent validation | 4,344 | About 3.9 days | 6 days |

Validation required a complete usable calibration handoff. Both phases used new,
disjoint cohorts. The disk launch reserves were 55 GiB and 35 GiB; working
copies are compacted only after verified publication or audited closure.
The host reboot showed that service startup did not provide task-level recovery.

[Finite release plan](HOST_CALIBRATION_RELEASE_PLAN.md) ·
[Continuation plan](VALIDATION_CONTINUATION.md) ·
[Previous campaign](FEASIBLE_PREDICTION_STATUS.md) ·
[Execution controls](execution-recovery/README.md) · [Next analyses](NEXT_STEPS.md).
