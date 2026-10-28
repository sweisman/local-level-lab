# Fresh calibration is prepared, not running

**The new release passes 98 software checks and has a frozen calibration
manifest. No fits have started.** It uses the
[qualified 48-case optimizer](../timing-matrix-combined/README.md) with unchanged
numerical code, physical bounds and error assumptions. All earlier campaign
allowances remain closed.

| Phase | Independent simulated families | Maximum fits | Estimated time on four threads | Proposed ceiling |
|---|---:|---:|---:|---:|
| Calibration | 299 | 7,176 | About 139 hours | 240 hours |
| Validation, only after calibration qualifies | 181 | 4,344 | About 84 hours | 144 hours |

That is about nine days in total, with a combined sixteen-day ceiling. These
are estimates; a failed numerical gate can stop a phase early without producing
a usable threshold. Both phases use new, separate seed ranges and preserve
unexecuted earlier cohorts as exclusions.

The purpose is to test how well prediction-error limits cover new simulated
examples. Calibration sets the limit; a separate validation cohort tests it.
Neither phase establishes an aircraft confidence level or adds another
Earth-model measurement. The 53 aircraft findings remain unchanged.

## Storage and safeguards

Require 55 GiB free before calibration and 35 GiB before validation. Measurements
from the preceding closed run suggest roughly 12–20 GiB of temporary calibration
case files and 7–12 GiB for validation; publication can temporarily duplicate
them. After verified archival and compaction, estimated retained payload is
about 5.2 GiB and 3.2 GiB respectively, plus metadata and archive overhead.

Keep four total numerical threads, the original 200-evaluation and 620-linear-
operation limits per fit, and zero retries. Stop cooperatively if both starts
fail a required calibration setting; validation stops at its fifth failed
family. Validation cannot start without a complete, finite, independently
audited calibration handoff under the same sources and environment.

## Prepared evidence

The execution freeze binds 253 source files and both phase policies. Tests cover
cohort exclusions, exact task and prepayment counts, unchanged inputs, the
combined qualification gate, failure handling, handoff rejection and disk checks.
The shared campaign preparer and workers are reused unchanged.

Calibration manifest SHA-256:
`40a06d0b54efe5107552df44e71de0a2b61d0af1802ac81998aca7b18cd30a13`.
Population SHA-256:
`3abeb0a1ad21c391fdbe0192a34d8cf3bc6bc47fc8783f331fe540c02055b992`.
The prepared start count is zero; the execution deadline begins only at launch.

[Full finite plan](../FEASIBLE_CALIBRATION_RELEASE_PLAN.md) ·
[Planning measurements](planning-estimate.json) ·
[Software test report](qualification-report.xml) ·
[Next analyses](../NEXT_STEPS.md).
