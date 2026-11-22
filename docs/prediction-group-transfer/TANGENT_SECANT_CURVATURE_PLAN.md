# Reuse trial tangents to estimate residual curvature

The [first native flight test](WEAK_CURVATURE_FLIGHT_RESULT.md)
used 181 training tangents without saving a forecast.
The small generated controls show that residual curvature can help,
while the flight-sized tangent makes probing every weak direction
too costly.

Use the difference between two tangents the solver already
evaluated. Hold the residual fixed, multiply the tangent difference
by it, and fit the symmetric rank-one curvature whose action
matches that difference along the actual step. Skip a correction
when the step and estimated curvature change are nearly orthogonal.
Start with Gauss–Newton curvature. Keep the last usable estimate
after an accepted step, and allow one model rebuild from an already
evaluated rejected trial at an unchanged point. Keep the direct
residual change and bounded strong-residual correction from the
previous small controls.

Test the same eight generated controls used by the
[weak-direction estimate](WEAK_TANGENT_CURVATURE_RESULT.md). Compare
to their sealed results. Require all eight to meet the unchanged
known-cost, parameter and fresh convergence checks. The new
calculation must use the secant and spend no calls on derivative
probes. Log every trial and verify the call count from the initial,
trial and fresh evaluations.

Allow eight starts, 40 evaluations per start, one worker, one
thread and a 60-second wall limit. The qualified finite interruption
policy is frozen separately. Save every result. No native forecast
or aircraft measurement enters this check. Further flight-scale
qualification needs its own freeze.
