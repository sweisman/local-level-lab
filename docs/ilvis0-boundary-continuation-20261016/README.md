# Continuing the timing-boundary diagnostic

This separate freeze runs only the twelve checks that never started in the partial
timing diagnostic. It reuses eight verified results, including both passing controls,
and leaves the interrupted ninth identity unresolved.

The [plan](PLAN.md) fixes twelve time-only starts and at most 312 native evaluations
on four numerical threads. Together with the reserved allowances of the earlier
starts, the combined ceiling stays at 546. No charged identity is retried.

The numerical method is unchanged. A separately qualified immutable receipt ledger
records each charge before execution. The old incomplete journal is not repaired.
The worker saves results and publishes its report automatically on completion.

Launcher: `analysis/tests/ilvis0_boundary_continuation_worker.py`. Runtime state is
in `data/ilvis0-boundary-continuation-20261016/`. `--package-only` publishes verified
completed outputs without fitting, prediction or decoding original measurements.

[Accounting audit](../ilvis0-accounting-audit-20261016/README.md) ·
[Software qualification](../ilvis0-receipt-qualification-20261016/RESULTS.md).
