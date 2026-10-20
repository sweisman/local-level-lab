# A better solver cannot fix these ranges by itself

All six saved cases produced exactly feasible examples. Across the 18 coordinate
ranges, their lower bounds differ from the existing upper bounds by at most
0.00000214 m. The search is therefore already very close to the best answer
the current linear prediction region permits.

Five coordinate ranges remain above the fixed target even at these verified
lower bounds. They cover the same three model/processing groups that failed the
previous comparison. Better optimization alone cannot make those groups pass
while keeping this region and its separate error allowances unchanged.

This is a diagnosis of the method, not a measurement of aircraft error. The
linear region deliberately allows some combinations of calibration and error
values that may not correspond to a physical sensor. The next check will test
that mismatch directly in the saved examples, starting with the matrix that
rotates and scales accelerometer observations.

All 36 LP proposals were used; the calculation finished in 3.7 seconds. Exact
rational checks verified every example after any needed repair. No original
recordings, native integrations, new aircraft fits or protected ESA outcomes
were used. The 53-stretch findings remain unchanged.

[Detailed results](README.md) · [Next check](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
