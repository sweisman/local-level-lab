# Matched observed timing trial

The packet-aware candidate must pass the complete, separately frozen
[67-control qualification](../ilvis0-timing-solver-qualification-20261016/README.md)
before this study starts. The candidate and the qualification result are
hash-checked before preparation and every observed identity.

The target is fixed: `fd7b81e48a4122b149c4925b`, under profiled removal and the
zero-background globe. Its [native timing checks](../ilvis0-timing-derivative-v2-20261016/RESULTS.md)
show the local prediction failing across a nearby packet boundary.

Four optimizer starts, no retries:

- One primary at the prior matched trial's failed primary endpoint, at most 200
  native fitting calls, including the original fresh final checks.
- One predetermined repeat, seeded by shifting each normalized primary coordinate
  by 0.01 toward the opposite sign, clipped to existing bounds; at most 200 calls.
- The same two completed controls, each at most 40 fitting calls.
- Two native diagnostic calls per identity. **Total ceiling: 488 native calls**.

Use one worker with four total numerical threads. All neighbor-interval predictions
and their native Jacobians count as fitting calls; no uncharged probes or restarts.
At the diagnostic's measured speed, the ceiling is roughly two to three hours;
actual completion may be earlier. Do not expand the allowance.

Reuse only the five hashed passing primary companions for this stretch from the
previous matched trial. Preserve original measurements, nominal integration clock,
initialization, receiver weights, calibration bounds and processing hypotheses.
The original fresh stationarity, objective-change and physical-position gates stay
unchanged. The only candidate change is how timing steps are proposed after a
rejected full bounded step. Local interval boxes are numerical subproblems, not
new physical restrictions on the allowed time offset.

Require both controls, the new primary, its repeat agreement and all five reused
companions before reporting a complete comparison. Keep saved failures and earlier
publications unchanged. A failed original gate remains a failure even at a genuine
packet-boundary minimum. No calibrated significance or wider rollout follows.

Freeze all sources, inputs, environment and original hashes before launch. Check
exclusive worker locks and completed dependencies. Pre-call journals retain failed
and interrupted starts; atomic hashed outputs support continuation of unstarted
identities only. Completed studies cannot restart. Publication performs no fits.
