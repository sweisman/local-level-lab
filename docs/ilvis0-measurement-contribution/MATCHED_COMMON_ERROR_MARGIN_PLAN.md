# Compare ranking and accuracy under additional shared GPS error

Reuse the four fixed NASA flight groups from the [matched forecast audit](MATCHED_FOUR_GROUP_AUDIT_RESULT.md).
Keep all original fit dispositions, all three receiver tracks and the full
withheld interval for each flight. Use the same local distance metric as
the earlier receiver spread checks. At every epoch, allow the common
reference position anywhere in the convex hull of the three receivers plus
an isotropic displacement of at most a fixed radius. The model forecasts
stay fixed. There is no assumption about how much error actually occurred.

Report the smallest additional radius that can tie or reverse each
available matched ranking and that can reach or exceed any fixed accuracy
limit. For absolute accuracy, find the farthest receiver vertex at each
epoch separately for horizontal and height error. An added displacement
can increase that distance by the full radius. Solve the resulting RMS
and maximum limits, keeping each limit's margin. Mark an already failed
limit at zero radius and preserve missing model comparisons.

For the reported specified-field globe preference, give the smallest
radius over both matched shape rankings, the field ranking inside the
globe family and the specified-field globe's accuracy limits, when all
are available. A missing comparison leaves this combined margin open.
This calculation gives a sensitivity margin for retrospective forecasts.
It leaves absolute aircraft error, independent coverage and the calibrated
decision rule open.

Use four local tasks with one worker and one thread. Allow one calculation
per existing forecast and matched ranking, a 60-second limit and zero
new fits, propagations or original measurement reads. Bind the companion
receiver data, fit statuses and source manifests to the saved group audit.
