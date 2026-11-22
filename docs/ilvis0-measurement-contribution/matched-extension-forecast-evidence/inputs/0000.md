# Test matched forecasts on the two added NASA flight groups

Use only the two windows selected before fitting in the [GPS
extension](GPS_RECONSTRUCTION_EXTENSION_RESULT.md). Require their [recorded
packet check](MATCHED_EXTENSION_INPUTS_PLAN.md) to pass under both clock
conventions. Use the nominal 200 Hz convention for this comparison, as in
the [initial preflight](MATCHED_OBSERVED_NUMERICAL_PLAN.md). Those earlier
fits, including any failure, remain separate from this study.

Fit all four shape and field combinations on each window. Use the same
calibration limits, receiver weights, normalization, wide tangent
arithmetic and stopping rules as the initial preflight. Start each fit
once from the original normalized origin. Fit only earlier GPS positions
and the associated inertial prefix. Save the later forecast from the full
inertial packet stream and query times before reading later receiver
positions. Require the original training-prefix agreement check.

Report the fit status and the later RMS errors in horizontal position,
height and total position for each of the three receiver solutions.
Where both shapes complete at the same retained field, report the two
shape rankings separately for that field. Report the globe field ranking
only where both complete shape comparisons favor globe in total position
on all three receiver tracks. Keep split rankings and missing fits visible.
The output describes retrospective predictions. Flight-level uncertainty
and a calibrated observed-data decision remain separate work.

Use eight one-start fits, at most 30 training evaluations and one forecast
each, up to 248 native calls. Use four one-thread workers with a 60-minute
cooperative limit. Keep the exact packet-visit budgets derived from the
verified inputs. Qualify task-level recovery before launch. Allow one
separately charged technical restart per unfinished task, up to two
interruptions and a 90-minute limit on the separate recovery stage.
Completed failed fits remain sealed.
