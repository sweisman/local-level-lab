# Match the trial-tangent estimator on the native generated flight

The [small trial-tangent controls](TANGENT_SECANT_CURVATURE_RESULT.md)
passed all eight starts without separate derivative probes. Test
whether that work reduction survives the full native forecast
pipeline. The [previous native candidate](WEAK_CURVATURE_FLIGHT_RESULT.md)
reached its wall limit before producing a forecast.

Reuse the same sealed 24-second specified-field globe case and
trust-region reference. Keep the 300 Hz header clock, all 26 fitted
parameters, first 15 receiver reports, eight withheld reports, and
zero start. Save the forecast before later positions are revealed.
The only changed component is the solver, which estimates residual
curvature from counted trial tangents. It uses the standard wide
native residuals, without the direct increment formula limited to
the small generated controls.

Use one new start, 200 training evaluations at most, the original
construction and forecast allowances, one worker, one thread, and
the same 210-second cooperative wall limit. Qualify only if the
unchanged fresh convergence and physical accuracy gates pass, the
training cost gap is at most 0.01, the withheld spread is at most
0.10 m, and at least one trial-tangent curvature update is recorded.
Check every training call against the initial tangent, logged
trial evaluations and fresh stopping calls. Keep interrupted work
under the separate qualified recovery allowance and retain any
failure. No observed or reserved flight data enter this test.
