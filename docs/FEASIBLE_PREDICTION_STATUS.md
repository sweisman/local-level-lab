# Prediction calibration is running

**The corrected prediction method is running its fresh calibration campaign
on four numerical threads.** Independent validation will follow only if the
complete calibration supplies a finite, independently verified error threshold.

| Phase | Independent simulated families | Maximum fit attempts | Expected time | Cooperative ceiling |
|---|---:|---:|---:|---:|
| Calibration — running | 299 | 7,176 | About six days | Ten days |
| Validation — conditional, not started | 181 | 4,344 | Another three to four days | Six days |

These examples have known simulated answers. Calibration establishes a
prediction-error limit; separate validation checks its coverage on new examples.
This work adds no aircraft measurements and does not yet establish confidence
for the original 53 aircraft comparisons.

## What changed before this run

The preceding calibration stopped at a numerical verification failure. Its
results and unused allowance remain closed. The solver correction now passes
the [complete 48-case qualification](timing-matrix-combined/README.md): all
cases, 24 starting-point pairs and four original-input replays. The new release
passes 98 software checks and freezes 253 source files and both phase policies.
The new cohorts exclude all earlier declared calibration and validation families.

Keep the original physical bounds, numerical limits and acceptance checks.
Every required setting must supply a usable fit. Calibration stops cooperatively
if both prescribed starts fail a required setting; validation stops at its fifth
failed family. Interrupted starts and failures remain recorded without retries.

## Storage and completion

Temporary case files are expected to use about 12–20 GiB during calibration and
7–12 GiB during validation. Publication can temporarily duplicate them. Verified
archival and compaction should retain about 8.4 GiB of payload for both phases,
plus metadata and archive overhead. Require 55 GiB free before calibration and
35 GiB before validation.

After calibration closes, independently audit and publish every returned and
unexecuted outcome, verify its hashes, then archive and compact recoverable
working copies. Prepare validation only from a complete finite handoff under
the same sources and environment. A stopped or failed calibration cannot launch
validation or supply a statistical claim.

[Full finite plan](FEASIBLE_CALIBRATION_RELEASE_PLAN.md) ·
[Preparation snapshot](feasible-calibration-preparation/README.md) ·
[Next analyses](NEXT_STEPS.md) · [Original aircraft findings](CURRENT_STATUS.md).
