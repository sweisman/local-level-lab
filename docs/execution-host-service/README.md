# Host-service lifecycle control

**Passed: the worker continued after the submission command returned.** A separate command observed three heartbeats while the service still owned its lease. The worker subsequently completed all eight heartbeats and sealed its result.

| Quantity | Result |
|---|---:|
| Metadata task starts | 1 |
| Completed tasks | 1 |
| Saved heartbeats | 8 |
| Worker duration | 16.1 seconds |
| Native or bound evaluations | 0 |
| Frozen source files | 35 |
| Adapter software checks | 7 |

The independently checked summary, journal, heartbeat order and source/environment bindings agree. A host-managed user service owned the existing study coordinator; automatic service restarts were disabled. The completed service was inactive and released its resources. No process was signaled.

This demonstrates survival of normal submitter exit in the tested arrangement. It does not demonstrate survival of a host reboot, execution-container reset or user-manager shutdown after logout. Unsaved optimizer state remains lost after such an interruption, and interrupted scientific starts may not be retried under the existing rules.

No aircraft observations or model fits were used. The [command-sandbox attempt](../execution-command-sandbox/README.md) retains its failed qualification. The interrupted calibration remains closed and supplies no uncertainty threshold.

[Execution-recovery plan](../CALIBRATION_RECOVERY_PLAN.md) · [Recovery software](../execution-recovery/README.md).
