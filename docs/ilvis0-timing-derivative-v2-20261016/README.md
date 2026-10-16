# Corrected timing diagnostic

The first timing check completed its control but rejected both target endpoints
before native evaluation because of one floating-point step beyond a parameter
bound. This separately frozen diagnostic corrects that endpoint construction and
reuses the completed control.

The [finite plan](PLAN.md) allows 24 native predictions on two saved endpoints,
with four numerical threads, no optimizer starts and unchanged scientific checks.
Every rounding adjustment is recorded; larger bound violations remain errors.
The current tally remains **47 globe preferences, zero flat and six unresolved**.

The diagnostic completed both endpoints and all 24 native calls in about seven
minutes, with no errors. The primary is about 23 ns before a common packet boundary;
the repeat is about 72 ns after it. Full and half coupled corrections predict a
decrease but increase the actual objective. See the [preserved results](RESULTS.md).
The next step is a [separately qualified packet-aware timing solver](../ilvis0-timing-solver-qualification-20261016/README.md).
This completed diagnostic cannot restart or reuse its allowance.

The launcher is `analysis/tests/ilvis0_timing_worker_v2.py`, through
`analysis/tests/run_numerical.py --threads 4`. Runtime metadata lives in
`data/ilvis0-timing-derivative-v2-20261016/`. `--prepare-only` freezes the study,
`--detach` launches it, and `--package-only` publishes completed evidence without
predictions. The preceding completed study cannot restart or reuse its allowance.
