# Fresh calibration preparation

**Prelaunch snapshot: 154 software checks pass and the 7,176-start calibration is frozen.** At this checkpoint no new fit had started. See the [current status](../HOST_PREDICTION_STATUS.md) for subsequent execution.

The source and input hashes, numerical environment, task matrix, four-thread allocation, original optimizer evidence and zero charged starts were independently checked. The freeze contains 260 source files. A single, explicitly pinned reporting update recognizes interrupted results; all other qualified numerical sources match the original optimizer evidence.

| Phase | Maximum fit starts | Workers × threads | Wall ceiling |
|---|---:|---:|---:|
| Calibration | 7,176 | 4 × 1 | 240 hours |
| Conditional independent validation | 4,344 | 4 × 1 | 144 hours |

The new cohorts exclude every previously declared cohort, including unused seeds. No closed allowance or lost start is reused. Both phases explicitly forbid interrupted outcomes from producing a handoff. The physical models, error process, calibration bounds, optimizer rules and per-fit limits are unchanged.

The [preparation report](preparation-report.json), [qualification report](qualification-report.json), [source/environment binding](qualification-request.json) and [test report](qualified-tests.xml) preserve the checks. Earlier preparation checks remain in the evidence inventory; they started no model fits. Public source/input snapshots are archived and recoverable, while the prepared runtime copies remain in place for execution.

The disk launch reserves are 55 GiB for calibration and 35 GiB for validation. They are free-space requirements, not permanent-retention estimates. Host-service execution survives normal submitter exit; host reboot and logout survival remain unestablished. No statistical threshold or aircraft detection is established by this preparation.

[Finite plan](PLAN.md) · [Current status](../HOST_PREDICTION_STATUS.md) · [Recovery controls](../execution-recovery/README.md).
