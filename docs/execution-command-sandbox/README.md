# Command-sandbox lifecycle control

**Survival of normal launcher exit was not demonstrated.** The launcher returned successfully, but no task start, heartbeat or worker completion was recorded. This attempt is closed and was not retried.

| Quantity | Result |
|---|---:|
| Planned metadata tasks | 1 |
| Charged task starts | 0 |
| Completed tasks | 0 |
| Native or bound evaluations | 0 |
| Declared launch window | 120 seconds |

The first later check found no heartbeat. At closure the journals still contained no task charge, and every lease was free. An empty worker log does not explain the cause. The result establishes no lifetime guarantee for a detached child in the command sandbox. No process was signaled.

The adapter's seven software checks passed before preparation. Frozen sources, input bindings and the closed allowance remain preserved. These are execution controls, not scientific model comparisons.

A [separate host-service control](../execution-host-service/README.md) tests a different execution arrangement. [Execution-recovery plan](../CALIBRATION_RECOVERY_PLAN.md).
