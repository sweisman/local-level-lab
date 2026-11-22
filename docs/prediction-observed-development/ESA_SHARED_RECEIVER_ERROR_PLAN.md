# Test sensitivity to an error shared by the ESA receivers

Use only the original 120 later receiver reports and six sealed
training-selected forecast paths from the two complete settings on
ESA development recording 187. Verify the same parent, forecasts and
reference scores as the previous receiver export comparison. The other
settings remain unresolved.

Find the smallest three-dimensional RMS change to the receiver path
that makes the disc tie or beat both globe forecasts. Do the same
for the zero-field globe against the disc and specified-field globe.
Allow any common correction vector at each epoch. Keep the local
metric fixed at the original receiver coordinates. A squared-distance
comparison in that frame is linear in the
correction. Check every possible active set of the two inequalities
and retain the shortest feasible correction. Verify that applying it
produces the reported score ordering. Test the calculation with exact
one- and two-boundary controls.

Separately find how small a path change could take the specified-field
forecast beyond each of the four descriptive position limits. Report
the nearest limit and the four margins. Allow arbitrary changes here
too, including a change concentrated at one report. Retain fixed
forecast paths and do not adjust calibration or weight the errors.

Run on one numerical thread, with zero new fits or propagations.
Keep the seven reserved flight groups closed. These are sensitivity
distances in metres. They are neither a measured receiver error bound
nor a probability, and they do not qualify the aircraft error law.

[Sealed forecast comparison](ESA_ALTERNATE_PPP_SCORING_RESULT.md)
· [GPS code cross-check](ESA_RINEX_CODE_COMPARISON_RESULT.md)
