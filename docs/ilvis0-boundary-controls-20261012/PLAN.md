# Boundary-aware nonlinear solver controls

This software qualification checks whether a solver can move along a parameter
boundary without prematurely stopping. It uses known mathematical answers, not
aircraft recordings. The completed archival studies remain unchanged.

The separate candidate in `analysis/lll/ilvis0_solver_boundary.py` takes bounded
linear least-squares steps, checks their actual nonlinear cost and shortens rejected
steps. It snaps only roundoff-sized distances from the box boundary. The final
fresh stationarity and bounded-stability checks retain their existing thresholds.

The fixed matrix compares the original rectangular solver, that same solver with
an exactly snapped start, and the new candidate. Each uses four predetermined
starts and at most 200 residual/tangent evaluations. Controls include interior and
boundary optima, redundant coordinates, unequal scales, nonlinear curvature,
gain/offset coupling and a 27-coordinate nonlinear problem with a condition number
of approximately 100 million. Every evaluation, including fresh checks, is counted.

Qualification requires known objective and predicted-observation recovery, fresh
stopping verification, feasible parameters and repeatability across starts. Unique
well-conditioned controls also require parameter recovery. Weak or redundant
coordinates are judged by predictions rather than an arbitrary parameter answer.
Competing methods are allowed to succeed; their failure is not a test requirement.

Tests are in `analysis/tests/test_ilvis0_solver_boundary.py`. A separate control
module and report builder preserve the comparison, source hashes and numerical
environment. Passing software controls alone authorizes no archival fits and
establishes no scientific result. A later observed trial needs its own frozen scope
and finite allowance.
