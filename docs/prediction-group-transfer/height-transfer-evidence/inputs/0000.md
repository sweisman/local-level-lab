# Check the height correction on seven other recording groups

Use all three groups from the [original two-cut study](../prediction-rolling-origin/RESULT.md)
and all four groups from the [first transfer study](RESULT.md).
These groups were left out of the [twenty-group drift test](ERROR_TRANSFER_RESULT.md).
Use only the matching header-clock, zero-removal setting and keep one
forecast per group and cut. Select the original passing start by earlier
training cost, or the lowest earlier training cost if both starts failed.
Preserve failed statuses.

Use the same earlier-only offset and slope in elapsed forecast time.
Apply the correction to height alone. Save it before scoring later receiver
positions. Report the changes at all seven groups and separately at the
three with passing starts at both cuts. North and east errors must stay
identical, and the original accuracy limits stay fixed.

This is a separate retrospective check within the same NASA archive.
It cannot establish independent-flight error coverage or recalibrate the
observational decision. Use seven charged correction calculations, one
numerical thread and a 90-second cooperative limit. Use no navigation
fits or new propagation.
