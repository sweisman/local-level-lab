# No shared set of the three variance scales fits these eight ESA windows

On ESA development flight 187, the same covariance has to explain both
the quietest steady window and the hardest turn. Across the **full
allowed range** of the steady and maneuver scales, their requirements
for the native variance multiplier do not overlap.

| IMU error description | Minimum multiplier required by turn 41116 | Maximum allowed by steady window 32716 |
| --- | ---: | ---: |
| Increment | 2.3159 | 0.1626 |
| Point rate | 2.3159 | 0.1626 |

Each bound allows the added terms to take values favorable to its own
window. Even then, the turn requires a multiplier more than 14 times
larger than the steady window allows. The calculation rules out a
common set of these three scales under the working error reference.
The earlier optimizer's stopping failures therefore cannot explain
the incompatibility. A different error structure or mean correction
would need to be fitted and tested on unused observations.
The [axis and time check](ESA_FORECAST_ERROR_LOCALIZATION_RESULT.md) finds
that north, east and height each suffice to expose the mismatch in the
hardest turn.

Both tasks passed their technical checks in 3.3 seconds on one thread.
The first rectangle covered the full ratio range and was excluded in
both cases, leaving no open rectangles. Each task used 16 distinct
linear solves with residual checks and floating-point margins. Eight
focused software checks passed. The result is retrospective and uses
a descriptive Gaussian reference on a single development flight.
No trajectory fit was run and the seven reserved flight groups remain
unopened.

[Frozen method](ESA_COMPONENT_SCALE_FEASIBILITY_PLAN.md) ·
[Bounds and charge-linked result](esa-component-scale-feasibility-result.json) ·
[Execution receipts](esa-component-scale-feasibility-evidence/README.md) ·
[Reproduction bundle](esa-component-scale-feasibility-evidence/bundle.zip)
