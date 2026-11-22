# First generated flight test of weak-direction curvature

The [eight generated controls](WEAK_TANGENT_CURVATURE_RESULT.md)
qualify the estimated curvature on small problems. A saved generated
flight tangent has 15 weak directions, so one iteration can require
30 tangent calls. The new test measures that cost in the native
training and prediction pipeline.

Use the complete specified-field globe case from the
[earlier generated flight comparison](CENTERED_FLIGHT_SOLVER_RESULT.md).
Keep its exact 24-second recipe, 300 Hz header clock, 15 training
reports, eight withheld reports, all 26 parameters and zero start.
Compare to the sealed trust-region result on those same inputs.
Run only one new fit. Other physical cases require a separate
qualification after this first test.

Use the weak-direction curvature estimate and strong-residual
correction, with the native wide residuals and no generated exact
increment formula. Keep the original fresh position and stationarity
check. Every Hessian probe, trial and final check uses a counted native
tangent call. Allow 200 training evaluations, the same bounded native
generation, covariance and forecast work as the matched reference,
one worker and one thread. The cooperative wall limit is 210 seconds.
Interrupted work uses the separately qualified recovery allowance.

The pair passes only when both fits pass the unchanged numerical and
physical accuracy gates, their training costs differ by at most 0.01,
and their withheld positions differ by at most 0.10 m at every report.
Save the forecast before revealing later positions. Preserve technical
and numerical failures. This first-stage test uses no aircraft
measurements or reserved groups and does not qualify observed work.
