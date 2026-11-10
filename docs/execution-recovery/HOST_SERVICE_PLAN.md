# Finite host service check

The command-sandbox launcher exited successfully, but its child produced no
heartbeat, task charge or completion. That attempt is closed and is not retried.
The host's user service manager is available. This separate check asks whether
it can own a finite worker independently of the command that submits it.

## Fixed allowance

One uniquely named service runs one study task with one worker and one reserved
thread. The task records eight heartbeats, two seconds apart. Its cooperative
wall allowance is 120 seconds. Native calls, bound evaluations, packet steps,
optimizer starts, measurement reads and noise draws are all zero. Retries and
automatic service restarts are disabled. The existing study runner provides
exclusive ownership, journals, frozen sources and sealed completion.

The service command uses a fixed project working directory and the existing
Python environment. Service creation is an action outside the workspace and
requires the execution environment's permission. No scientific campaign is
included in that permission or in this allowance.

## Acceptance

The submission command must return while the worker still has work remaining.
A subsequent, separate command must observe heartbeat progress and verify all
eight saved heartbeats and the sealed passing result. The journal must contain
exactly one metadata task start and zero native or bound work. All source and
environment bindings must match, with no retry of the command-sandbox attempt.

This can establish survival of normal submitter exit under a host-managed user
service. It cannot establish survival of a host reboot, recover unsaved optimizer
state or prove that the user service manager stays active after logout. Those
lifetime limits must be stated before another multiday proposal.
