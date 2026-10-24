# Efficient charging for long error calculations

The native training adapter is software-qualified. Before running long noisy
fits, avoid a durable database transaction for every IMU packet. Charge a finite
block of work in advance, then check each attempted call against that block in
memory. This changes bookkeeping, not the motion or error model.

Use the existing shared study journal. New SQLite records may reserve several
native operations with one transaction, recording both the operation count and
total packet visits. Historical records still mean one operation. Status,
merging and audit must count operations rather than database rows.

An interrupted block keeps its entire charge. Its unused work cannot be
refunded, retried or borrowed. Each call must stay inside both prepaid limits.
Keep process/thread ownership, reject use after exit, check cooperative stop
requests at entry and at least every 128 calls, and forbid sealing a task with
an active block. Keep ordinary single-call and historical receipt behavior.

Qualify at most 32 new deterministic accounting checks, plus the affected
journal, runner, allowance and status regressions. Use one numerical thread,
no native builds or calls, no optimizer starts and no aircraft measurements.
Run the complete source-bound qualification under a fresh request/report;
preserve failures. No completed study is converted or restarted.

Then freeze separate noisy nonlinear fitting controls. Protected confirmation
recordings remain unavailable to development.
