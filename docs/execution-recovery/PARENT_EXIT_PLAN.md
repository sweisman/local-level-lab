# Finite launcher exit check

This software check asks whether one harmless study worker continues after its
launching command exits normally. It does not test a host restart, a lost
execution container or recovery of unfinished optimization state.

## Frozen scope

- One study, one task, one worker and one reserved thread.
- Eight two-second intervals, with a saved heartbeat after each interval.
- A 120-second cooperative wall allowance; zero native calls, packet steps,
  bound evaluations, optimizer starts, measurements or noise draws.
- No retries, process signals, replacement results or calibration work.
- The existing `lll.studies` definition and runner provide source/input hashes,
  environment binding, the charge journal, leases and sealed completion.

The adapter is the shared `lll.studies.execution_probe` component. Its seven
deterministic tests must pass before preparation. The launcher redirects logs
to the study directory and starts the existing coordinator in a separate
session, then exits. A later command must observe heartbeat progress after
that exit and verify the study's sealed completion, exact task count and zero
native charges. The launcher's successful return is recorded separately from
the worker's result.

Passing demonstrates normal launcher-exit survival in the tested environment
only. It does not authorize another multiday calibration or promise survival
of a host or container reset. The stronger execution arrangement must be
established separately.
