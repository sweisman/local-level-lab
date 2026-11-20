# Check the saved aircraft forecasts against a shared GPS uncertainty region

Use the six sealed forecasts and their original later GPS fixes. Preserve
both missing zero-field disc forecasts. Score 30, 60 and 120 seconds after
the last training fix, and the full saved forecast. Use one north/east/up
coordinate scale from onboard GPS at each epoch for every candidate and
receiver solution.

At each epoch let the reference range over the convex hull of the three
saved GPS solutions. Find the smallest and largest possible horizontal and
height error for each forecast. Allow the mix of GPS solutions to vary by
epoch. For paired squared errors use the same reference for both forecasts.
The paired difference is linear in the reference, so its extremes occur
at the three vertices. Report the additional common position-error radius
that would allow a tie. Score the same-field shape contrast before the
within-globe field contrast, which remains a descriptive comparison.

This is a sensitivity calculation on a measured GPS spread. The three
solutions share satellite observations and may share position error. The
hull gives no bound on real receiver error or physical adequacy. Use the
two recorded stretches, at most 371 later receiver epochs and at most six
saved forecasts, with one numerical thread. Run no new fits or receiver
solves.
