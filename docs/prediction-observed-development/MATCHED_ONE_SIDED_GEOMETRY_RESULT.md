# Straight and turning routes: three matched model fits each

The [finite generated study](MATCHED_ONE_SIDED_GEOMETRY_V2_PLAN.md) completed
both routes and all six fits. Each route supplied the **same generated IMU
measurements and earlier receiver positions** to rotating globe, stationary
globe and stationary disc. Later receiver positions were opened only after
all three forecasts and their ranges were saved. The new one-sided numerical
rule was applied equally to every candidate.

| Route | Candidate | Numerical fit passed? | Earlier full-correction check passed? | Withheld horizontal error | Withheld height error |
| --- | --- | --- | --- | ---: | ---: |
| Straight | Rotating globe | Yes | Yes | 2.74 m | 1.11 m |
| Straight | Stationary globe | Yes | Yes | 13.24 m | 0.68 m |
| Straight | Stationary disc | Yes | Yes | 10.39 m | 1.17 m |
| Turning | Rotating globe | Yes | Yes | 3.07 m | 0.51 m |
| Turning | Stationary globe | Yes | Yes | 4.07 m | 0.68 m |
| Turning | Stationary disc | Yes | Yes | 4.31 m | 0.54 m |

The errors are root-mean-square differences over later receiver positions;
they are not calibrated accuracy thresholds. Every candidate's saved
whole-path range contained the later receiver path on both routes. The
model comparison therefore **abstains on both routes**, even though the
rotating-globe forecast center is closest horizontally in these two
generated cases. The ranges remain too broad to separate the candidates.

All six original full-correction checks also passed. Thus this particular
matched comparison verifies equal application of the new rule but gives no
case where that rule changes an old verdict. The earlier two noisy turning
fits remain the examples where it does. Neither numerical convergence nor
range containment establishes that the assumed aircraft error law is
accurate, that the forecasts are physically adequate on real flights, or
that any Earth model has been detected. The next work is to qualify a
source-specific receiver/IMU error model and an absolute withheld-prediction
criterion before opening independent aircraft groups.

The [verified machine report](matched-one-sided-geometry-result.json) binds
these figures to the sealed six-fit study, its source and plan hashes, input
bindings, original and new stopping verdicts, and charged work. The corrected
short preflight completed technically but its three fits did not converge
within 18 evaluations. An earlier preflight failed before native fitting
because of an input-layout error; it remains recorded separately. Neither
preflight was counted as a scientific comparison.
