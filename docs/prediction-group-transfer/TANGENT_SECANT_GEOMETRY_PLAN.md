# Match both remaining native geometries before a solver release

The [specified-field globe control](TANGENT_SECANT_FLIGHT_RESULT.md)
passed. Test the other two generated geometries independently
against the trust-region solver. Keep the original 24-second
recipes, 15 training reports, eight withheld reports, all 26
parameters, and zero start. Use the zero-field globe at nominal
200 Hz and the disc with generated 300 Hz header timestamps.

The [earlier centered-solver study](CENTERED_FLIGHT_SOLVER_RESULT.md)
left both trust-region references unstarted. Verify that status
and start one fresh trust-region and one trial-tangent fit per
geometry. Within a pair only the solver changes. Use the same
native residual representation as the first trial-tangent case
and save each forecast before reading the generated later positions.

Four single-thread workers each execute one task. Allow 200 training
tangents per fit and the unchanged generation, covariance and forecast
allowances. The cooperative wall limit is 210 seconds. Freeze the
existing finite interruption recovery policy. Keep every attempt,
including incomplete forecasts. Do not start this work while
unrelated numerical threads are in use.

Each pair needs complete matched training inputs, unchanged fresh
stopping and physical-accuracy passes, cost gap at most 0.01,
and maximum withheld position difference at most 0.10 m.
Require use of trial-tangent curvature and zero separate curvature
probes. Both pairs must pass for a three-geometry short-control result.
A pass would still leave longer and more difficult generated cases
and observed-aircraft qualification open. No original flight or
reserved observation enters this test.
