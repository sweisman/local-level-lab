# Efficient native-work accounting

**All 112 checks pass**, including 18 new checks for prepaid blocks of native
calculations and 94 journal, runner, allowance and status regressions.

Long error calculations can now reserve a finite block once and check each
attempt in memory. This avoids a durable database transaction for every IMU
packet. Status and merging count the reserved operations, rather than confusing
one database row with one calculation. No numerical speedup factor is claimed.

Every block remains bounded. Interrupted or partly used blocks keep their full
charge. Nested blocks, use by another process/thread, use after exit and sealing
an active block are rejected. Cooperative stop checks occur at entry and at
least every 128 attempts. Historical single-call records retain their meaning.

The [receipt](evidence-receipt.json) preserves the exact sources and test report;
all 37 artifact hashes are verified. These are bookkeeping tests with zero
native calculations, builds, optimizer starts or aircraft measurements.

[Plan](../ACCOUNTING_PLAN.md) · [Training adapter](../training-adapter-qualification/README.md) ·
[Error propagation](../README.md).
