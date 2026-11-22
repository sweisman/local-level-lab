# Check the ESA forecast error against three GPS solutions

The [window-scale comparison](ESA_WINDOW_SCALE_MIXTURE_RESULT.md)
left one steady window outside its reference. Check whether that outcome
depends on which GPS receiver's position solution is used. Use the eight
fixed forecast windows on ESA recording 187 and the two other GPS-only
position exports from the same flight. All three receivers share an
antenna. Agreement can test differences between receivers and processing
streams. Shared GPS errors and coverage on other flights remain open.

Verify each original file against the
[full-flight comparison](FULL_PARALLEL_GNSS_V2_RESULT.md). Check the
original scoring positions against the `air1` export. Match the two other
receiver exports at the same epochs using the original two-millisecond
tolerance and the same first-order correction from reported velocity.
Convert the receiver differences to the archived forecast's north, east
and height scales. Require complete matching at all 120 reports for each
comparison. Retain missing matches as unavailable without filling them in.

Keep each forecast, the Gaussian covariance parameters and the degrees of
freedom from the donor-only selection fixed. Reproduce the saved Gaussian
and Student scores against `air1`. Compare the quadratic score and Student
reference check against each alternate receiver. Report signed changes,
receiver differences by axis and every change in whether a window is within
the reference. This diagnostic does no fitting and applies no new scientific
acceptance rule.

Freeze the signed receiver differences, matched times, saved windows,
software checks, source and environment hashes. The one-thread preparation
reads only the three known exports for recording 187, once to hash and once
to parse, with two disjoint forecast input conventions. Use eight paired
tasks and two one-thread workers, at most eight score charges and ten charged
steps per task, zero trajectory fits and a 180-second cooperative wall
allowance. Recover interrupted work through the qualified task runner under
a separate 180-second allowance with one further attempt per unfinished task.
