# Diagnosing the six remaining stretches

This study tests a specific numerical obstacle: the stopping calculation crossing
an IMU packet boundary. It covers all nineteen unfinished fit endpoints across
the six stretches, with two passing controls first.

The [plan](PLAN.md) fixes the computation at 546 native evaluations maximum,
four numerical threads and no retries. Software and compiled-motion controls have
passed. The worker preserves earlier results and publishes its diagnostic report
automatically on completion. No scientific disposition changes merely because a
local boundary check passes.

Launcher: `analysis/tests/ilvis0_boundary_diagnostic_worker.py`. Runtime state is
kept in `data/ilvis0-boundary-diagnostic-20261016/`. `--package-only` copies verified
completed results without predictions, optimization or original-data decoding.
