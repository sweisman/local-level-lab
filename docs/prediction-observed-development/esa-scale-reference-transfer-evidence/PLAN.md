# Test continuous ESA scale settings against the fixed error reference

Use the eight saved forecasts and both inertial measurement error laws from
the [continuous compatibility check](ESA_AXIS_SCALE_COMPATIBILITY_RESULT.md).
Keep forecast means, added covariance roots, motion response, the six
innovation scales, their limits and the two-sided joint error reference.

Choose the quiet and motion log scales that minimize the largest deviation of
any included window's quadratic score from the center of the reference. Measure
each deviation in units of that window's reference half-width. Use two starts
and at most 96 evaluations per start. Choose the best evaluated point even if
the numerical solver stops. Bracket each chosen score independently using the
covariance solve residual, then verify it with the original likelihood. A
candidate is compatible only if every checked interval lies inside the original
reference. Failure to find a candidate leaves compatibility unresolved.

Check all eight outcomes together once per error law. Start at the steady
witness with the median earlier motion coefficients, and at the coordinatewise
median of the archived axis-scale settings. Check any all-window witness
against the open boxes of the completed continuous compatibility search. This
is a retrospective check of whether the model family has enough flexibility.

Separately leave each original turn-and-steady pair out, without using any
result selected from its outcomes. Use the two archived settings from that
fold's six donors as starting points. Estimate continuous scales on those
donors, then score both omitted windows using the frozen scales. Retain the
earlier separate-quiet-scale scores for reference. For the within-flight screen
to pass, all eight omitted windows must meet the working error reference under
both laws and the total negative log score must improve over the earlier
separate-quiet rule. A pass does not establish between-flight coverage.

Freeze ten tasks with two single-thread workers and a 180-second cooperative
limit. Bind the existing tested recovery policy with a 240-second recovery
allowance. Test the covariance score derivative, finite evaluation allowance
and compatibility on a known example. Make no new trajectory fits, receiver
reconstructions or confirmation-flight reads.
