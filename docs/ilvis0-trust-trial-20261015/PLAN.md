# Finite matched archival trial

The revised hybrid solver passed all 48 checks in its separately frozen software
qualification. This trial permits **eight starts and at most 1,296 native sweeps**,
with four total numerical threads, no retries and no wider rollout.

The targets are exactly the three original budget-continuation targets:
`2a56eb8fa7d4e10c9a867bb0`, `7df21c836bec5751f83c0cce` and
`fd7b81e48a4122b149c4925b`. Only their originally failed model/case identities are
refitted. Each primary starts at its latest frozen primary endpoint. Each scheduled
repeat starts from that same endpoint perturbed inward by 0.01 in normalized
coordinates; previous repeat outcomes never select a start. Fifteen passing
companion primaries are reused with hashes. Two completed controls are refitted.

The three primary/repeat pairs allow 200 fitting calls each. The controls allow
forty each. Every start also allows two diagnostic predictions. Original observations,
intervals, physical models, covariance, clock, calibration bounds and final acceptance
gates are unchanged. All six matched primaries, the target's repeat agreement and
both controls must pass before its disposition can change. A passing repeat never
replaces a failed primary. Every charged interruption remains spent.

At the preceding matched run's measured 16 seconds per native sweep, the ceiling
is about **5.8 serial hours**. This is a finite comparison, not permission to
spend unused prior allowances, retry failures or launch a corpus-wide recovery.
Source/input/environment hashes, immutable identities, start/sweep journals,
atomic artifacts and exclusive locks are frozen before execution. Publication
performs no fits. Completed studies cannot resume.
