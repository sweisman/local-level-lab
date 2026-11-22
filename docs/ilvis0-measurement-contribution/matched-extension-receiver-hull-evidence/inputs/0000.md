# Check the new forecast rankings across the measured GPS spread

Use the eight already saved forecasts from the [two added NASA flights](MATCHED_EXTENSION_FORECAST_RESULT.md).
At each withheld report, allow one shared position anywhere between the
three GPS solutions in the same local metric. Use that position for every
model at that report. Allow it to vary freely from report to report. This
checks a wider range than using each GPS stream as a whole. It leaves
errors common to all three streams outside the measured spread.

Repeat the [original receiver sensitivity check](MATCHED_IMU21_RECEIVER_HULL_RESULT.md)
on both flights. Test the same four model pairs on the horizontal, height
and 3D errors at 30, 60, 120 seconds and the full withheld interval.
Report any pair whose ranking can reverse. Report the minimum extra shared
displacement outside the measured spread that can bring a comparison to a
tie under this error calculation.

Check whether each forecast meets the same fixed accuracy limits over
the entire spread. For each report and metric, use the largest error
across the vertices of the measured GPS triangle. The maximum is at a
vertex because the squared error is convex in the shared position. Since
the position can vary independently at each report, these maxima give
the worst RMS and peak errors in this local metric. The limits remain
10 m horizontal RMS, 30 m height RMS, 50 m peak horizontal error and
150 m peak absolute height error. This checks descriptive accuracy and
does not estimate error coverage across independent flights.

Use one task per flight, 48 paired ranges and four accuracy checks per
task, zero new fits and zero propagations. Use one worker and one thread
with a 60-second wall limit. Freeze the exact saved forecasts and GPS
coordinates, and preserve any incomplete outcome.
