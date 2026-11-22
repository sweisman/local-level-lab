# Does smooth path error explain the later score increase?

Reuse the two earlier-only specified-field globe forecasts at each of the
200 and 400 report cuts from the [same-flight scale check](ESA_ROLLING_SCALE_TRANSFER_RESULT.md).
Use the same four error laws, receiver rows and weighted whole-path score.
Recover all sixteen original scores before decomposing them.

For each 120-report forecast, compare its remaining error with constant,
linear, quadratic and cubic changes in the three position coordinates.
Project each nested set of changes in the same conditional covariance
metric used for scoring the forecast. The cubic basis allows a constant
offset, velocity, acceleration and jerk in the diagnostic error. Preserve
the whole error and the remainder at each degree. Compare the later-to-earlier
score ratio before and after these projections.

The projections inspect the withheld positions. They are descriptions
of what the saved forecasts missed and do not train a new forecast,
estimate an error covariance or attribute any residual to a specific sensor.
Use the two sealed forecast studies and saved scores, one thread, eight
error operators and sixteen decompositions. Allow zero fits, new data
acquisitions or protected reads.
