# Final-stretch specified-field boundary checks

The remaining stretch `b4e44ddc0f130ecd45674c78` has two separate numerical
problems. Its specified-field-globe primary/repeat solutions agree closely in
cost and predictions, but their boundary checks include unstable calibration
corrections and unchecked neighboring boundaries. Its zero-field-globe solutions
differ by about 57 ms and exceed the required repeat-cost tolerance.

Apply the already qualified range-scaled affine correction and representable-clock
checks to the four complete original specified-field endpoints, under both
processing assumptions. This tests a known local numerical defect before the
larger nonlinear timing-profile problem. It does not retry the earlier algorithm,
resume an old identity or spend a completed allowance.

## Exact scope

Only `sphere_rotating`, `bias1_unsubtracted` and `bias1_profiled_removal`,
primary and repeat. Preserve each original full endpoint, observation interval,
clock, covariance, physical bounds and unknown-processing assumptions. Reuse the
qualified saved-context adapter, checking exact receiver rows and relative times
before extraction. Two fresh smooth controls run first.

| Item | Maximum |
|---|---:|
| Fresh controls | 2 × 3 native calls |
| Four target boundary checks | 4 × 26 native calls |
| Charged identities | 6 |
| Native calls | **110** |
| Nonlinear optimizer starts | 0 |
| Clock queries | 804,096 |
| Bounded affine solves | 10 |
| Total numerical threads | 4, one worker |
| Retries | 0 |

The preceding matched study used 54 calls in 1,728 seconds, about 32 seconds per
call including extraction and checks. At that rate this ceiling is approximately
59 minutes; runtime can differ with the recording and early stopping. It is an
estimate, not permission to exceed the fixed evaluation allowance.

Qualification is one 34-test batch with a 120-second ceiling: the existing 30
scaled-candidate controls and four exact-scope/worker checks. The existing
candidate controls include both saved failure systems, three independent
compiled-motion controls and six compiled clock comparisons. No original-file
reads or observed native calls occur during qualification.

Seal the exact tasks, original hashes, source snapshots, qualification, kernel,
numerical environment and this plan before launch. Check locks and receipts;
charge before execution, preserve failures and block any incomplete transaction.
Never restart completed work or retry a charged identity. Finite limits cannot
be expanded while running or after completion.

All targets require unchanged full two-sided native gates and cumulative
source-to-final movement checks. Compare primary and repeat separately for each
processing assumption, retaining the relative-cost limit 10^-6 and per-axis track
RMS limit 0.01 m. Both controls and both pairs must pass full qualification.

Even a complete pass cannot resolve the stretch: the zero-field-globe timing
profiles, required repeat comparisons and all other model/case companions remain
necessary. Keep the current **52 globe / 0 flat / 1 unresolved** count unchanged.
The subsequent zero-field profile requires its own finite freeze.
