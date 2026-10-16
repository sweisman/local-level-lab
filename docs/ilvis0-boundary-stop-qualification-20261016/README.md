# Two-sided stopping checks for the remaining six stretches

All six unresolved stretches have fits that stop at closely spaced IMU packet
boundaries. A smooth correction can cross a boundary and worsen a fit even when
the endpoint is a real local minimum.

This candidate checks both feasible sides, allowing every nuisance parameter to
move within its original bounds. It retains the existing cost and physical-position
tolerances and requires fresh actual predictions. Maxima, unfinished nuisance
fits, discontinuities and one-sided failures must remain failures.

The [finite qualification plan](PLAN.md) fixes 43 independent software checks, one
sealed batch, four numerical threads and no archival reads or fits. This is a
new numerical policy candidate for an exact, supplied timing knot. The real
archive's cluster of nearby knots requires a separately checked adapter before
the candidate can be tested on observed data. No existing result is relabeled.

The sealed batch passed **43/43**, with zero failures, errors or skipped checks.
See the [qualification results](RESULTS.md). The [saved-clock applicability screen](../ilvis0-boundary-adapter-preparation-20261016/README.md)
finds supported side geometry for every unfinished primary and repeat. Its
[next diagnostic plan](../ilvis0-boundary-adapter-preparation-20261016/NEXT_PLAN.md)
targets all six stretches, with native adapter qualification still required.

Candidate: `analysis/lll/ilvis0_boundary_stop.py`.
Worker: `analysis/tests/ilvis0_boundary_stop_qualification_worker.py`.
The completed-study runtime directory is
`data/ilvis0-boundary-stop-qualification-20261016/`; a completed batch cannot restart.
