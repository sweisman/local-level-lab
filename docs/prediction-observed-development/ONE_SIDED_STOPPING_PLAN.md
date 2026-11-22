# Candidate one-sided stability check: software qualification only

## Why this is separate

The original full-correction check requires the *absolute* change in cost to
be below 10⁻⁸ relative. On the two generated turning cases, the full bounded
linear correction predicts a tiny cost decrease but actually increases cost.
Two independent bounded methods return virtually the same cost. A cost
increase at a nearby point does not establish a better solution elsewhere;
nor does it justify relabeling a historical fit. This plan tests a new,
versioned numerical check without touching the original one.

## Candidate rule

At a feasible point, retain the original projected-stationarity threshold,
bounded linear correction, fresh residual/Jacobian evaluation, 1 mm RMS and
1 cm maximum physical-position stability limits. Evaluate the original full
correction and six predeclared fractions: ±1/2, ±1/4 and ±1/8. Also repeat
the baseline point to check deterministic evaluation. Require every tested
point to remain within the physical-position limits and have no actual cost
*decrease* greater than the original 10⁻⁸ relative threshold. A cost increase
alone does not fail this candidate check. Record the original full-correction
check alongside it. This is a local numerical check, not proof of a global
optimum or an absolute model adequacy test.

## Qualification and limits

First run cheap deterministic tests: exact interior and boundary optima,
weak/redundant directions, a nonstationary feasible point, a point with a
detectable descent direction, a physically unstable correction, and an
inconsistent repeat. The same test policy applies to every physical model;
no candidate name or outcome enters the rule. The software checks must pass
before any new fit uses it.

Any later generated fitting study must have a separate source/environment
freeze, known-answer qualification, finite maximum starts and native calls,
task-level reboot recovery and all original acceptance labels preserved.
No observed-aircraft or protected ESA fit is authorized by this plan.
