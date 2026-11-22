# Check the matched-field shape score across receiver solutions

Use the fixed 400 earlier and 120 later times from development flight 187.
Compare the zero-field globe and stationary-disc forecasts selected by
the original increment-error fit. Reuse their saved coordinates, the
earlier reference chart, the matched-field shape direction and its
working covariance with a 3 cm white receiver term. Reproduce the archived
projected model separation before judging any receiver effects.

Use exactly eight existing receiver paths. These are the original export,
the two GPS code solutions, the final GPS orbit replay, the broadcast GPS
solution with G17 omitted, the clock-change solution on that same set,
and the two GLONASS code solutions. Reuse the exact earlier and later
epoch assignments from each comparison. Keep the original fitted
calibrations and covariance fixed. Compare the score contributions from
changed earlier receiver positions and changed later receiver positions.

Project both model residuals away from the nine free smooth corrections
in the original shape comparison. Report the midpoint score in the
direction from globe to disc, along with each model's remaining squared
error. A negative score is closer to the globe forecast within this
comparison. Check the squared-error difference against the direction
score. Do not interpret these values as calibrated probabilities.

The saved-only diagnostic allows eight receiver paths on the final fixed
support, one archived covariance restoration, zero fit starts and zero
forecast integrator calls. It reads only the previously opened position
reports on recording 187. The covariance and absolute adequacy criteria
still require qualification before any independent group is opened.
