# Testing the time-alignment derivative

The current recovery total is 47 globe preferences, zero flat preferences and six
unresolved stretches. The remaining failed fits stop early. This focused check
asks whether the fitted timing direction predicts actual position changes across
nearby IMU packet intervals.

The [finite plan](PLAN.md) fixes three saved endpoints and at most 34 native
predictions, with no optimization. It preserves all scientific results and limits.
Software controls check the derivative comparison, packet convention, feasibility
and exact call counts before launch.

This run has finished: the control completed ten native calls, while both target
identities failed preflight before native evaluation. Their saved coupled
corrections exceeded a normalized bound by one floating-point step. The errors
and [results](RESULTS.md) remain preserved. A [separate corrected freeze](../ilvis0-timing-derivative-v2-20261016/README.md)
reuses the completed control and tests the two previously unevaluated endpoints.
This completed run cannot restart or spend its unused allowance.

The worker is `analysis/tests/ilvis0_timing_worker.py`, invoked through
`analysis/tests/run_numerical.py --threads 4`. Runtime state and source snapshots
are kept in `data/ilvis0-timing-derivative-20261016/`. `--prepare-only` freezes inputs;
`--detach` starts the finite diagnostic; `--package-only` publishes completed
results without numerical predictions. No completed identity may be retried.
