# Matched packet-aware timing trial

This four-start comparison tests whether respecting IMU packet intervals helps the
previously diagnosed stalled fit. It uses the same measurements and physical
assumptions, with the original final acceptance checks.

The [finite plan](PLAN.md) fixes one failed primary, its scheduled repeat and two
completed controls: four starts, at most 488 native calls, four numerical threads
and no retries. Five passing companion fits are reused with their hashes verified.
The [software qualification](../ilvis0-timing-solver-qualification-20261016/RESULTS.md)
must pass before launch. No result is changed by preparation.

Launcher: `analysis/tests/ilvis0_timing_trial_worker.py`, through
`analysis/tests/run_numerical.py --threads 4`. Runtime metadata and source snapshots
are in `data/ilvis0-timing-trial-20261016/`. `--prepare-only` freezes the study;
`--detach` launches it; `--package-only` publishes completed evidence without fitting.
The current published tally remains 47 globe, zero flat and six unresolved.

The trial is complete: **four starts / 237 native calls**, about 70 minutes.
Both controls passed; the target primary and repeat failed the unchanged fresh
stability gate despite agreeing in predicted track to about one micrometre.
No additional stretch was resolved. The candidate did not qualify for wider use.
See the [sealed results](RESULTS.md). This completed study cannot restart or
reuse its unused allowance.
