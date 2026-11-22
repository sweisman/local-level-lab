# Check the field-range result across receiver exports

The [field-range result](ESA_DIRECTION_HOLDOUT_FIELD_RANGE_RESULT.md)
sets a direction-accuracy target. With the primary receiver predictions
held fixed, less than 0.0080° RMS of angle error would preserve all 64
shape rankings. Test how much changing receiver processing spends of that
margin on the same eight windows. The receiver exports share an antenna.
Their differences measure processing sensitivity and leave shared errors
unmeasured.

Use the two alternate exports from the opened recording 187, `mosaic03`
and `pwrpak7`. Require the source sizes, hashes, row counts and printed
counter behavior from the [earlier receiver audit](FULL_PARALLEL_GNSS_V2_RESULT.md).
Match every selected one-second report within 2 ms of the primary time.
Retain the actual alternate timestamps during differentiation and use
the original primary time kernels for predictions. Keep all eight
windows and report missing coverage explicitly. Use the recorded angles,
antenna settings, field range, differentiation methods and widths from
the original check.

Evaluate zero physical field separately and the full retained fraction
range at the same 81 grid points with the same between-grid error bound.
For each alternate export compare the interval for the best globe error
with the interval for the best disc error. Report the shift in predicted
angles against the primary export at the three original field settings.
Keep the earlier absolute error references and field-range comparisons
separate. A small change at the endpoints leaves intermediate predictions
unchecked by that particular shift statistic. The continuous score bound
is calculated separately for each export.

Freeze two tasks, one per alternate file. Each task may hash its declared
file once, parse up to its exact published row count once, and charge
16 window/width operations with the same finite quadrature allowance as
the primary field-range check. Use one worker and one numerical thread
with a 225-second ceiling. Preserve each task and checked window receipt.
The only original files read are the two alternate receiver exports.
Use sealed inertial angles and primary receiver predictions. There are no
new calibration fits or reserved-group reads.
