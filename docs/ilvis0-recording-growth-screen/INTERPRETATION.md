# The longer-input calculation runs, but its ranges are still too wide

**All six numerical cases pass in 38.5 minutes.** Each retains the complete
four-minute generated input and tests its original 50-second endpoint under
the full calibration domain. The study used 24 native queries and six bounds;
there were no aircraft observations, model fits or retries.

The new full-domain outer radii are about **71–72 km**. These are conservative
ranges when no training observations constrain calibration, not measured flight
errors or prediction confidence intervals. Passing the arithmetic/probe checks
does not make these ranges useful.

The two matched historical globe cases also show why approximation error and
the full range must be reported separately. Their older whole-change bounds
have maximum radii about 28.7 km, compared with about 72 km in the new expression.
The new unshared remainder is much smaller, but the sum of its unconstrained
shared terms is wider. This decomposition is not an improvement in the total
unconstrained range. Preserve both kinds of bound rather than discarding the
older one because one new error term is smaller.

The next recording-length study needs constraints derived from its own training
observations, complete coverage, supported numerical treatment and an explicitly
justified observation-error allowance. It must cover the intended full history
and integration-clock uncertainty. This fixed-clock screen cannot qualify those
requirements or open new aircraft prediction fits. All 53 empirical comparisons
remain unchanged.

[Verified numerical results](README.md) · [Frozen scope](PLAN.md) ·
[Recording-length requirements](../ilvis0-three-source-complete/NEXT_PLAN.md) ·
[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
