# Revised trust-region qualification

One separately frozen batch: 48 known-answer tests, at most 8,286 software evaluations, four numerical threads, ten minutes, zero archival starts and no retries. All tests must pass. The same forty analytic, six raw-increment motion and two negative controls are retained from the earlier failed qualification.

The candidate tries the full bounded Gauss–Newton correction before a trust-region fallback; damping is reserved for an unfinished local solve. Final undamped stationarity, objective and position checks are unchanged. The earlier candidate and its failures remain frozen.

If qualified, a separate eight-start matched archival trial will use the three original budget-continuation targets, their primary endpoints, predetermined repeats and two controls. It permits 1,296 native sweeps, no retries and no wider rollout.
