# Compare acceleration estimates with the RF04 reference receiver

Use the same 383 RF04 centers and earlier/later assignments as the
force-average comparison. Extract the reference receiver's reported north
and east velocity from the exact previously verified RF04 netCDF file.
Require receiver status OK and complete, finite velocity at every retained
RF04 second. Preserve the original record and its hash. Keep avionics and
inertial navigation channels outside the calculation.

For windows of 2, 6 and 10 seconds, divide the receiver's endpoint change
in north/east velocity components by the elapsed time. Predict the same
quantity for both saved RF04 flight-stretch paths by differentiating the
original quartic position windows. Use the WGS84 coordinate scale at each
endpoint so both predictions can be compared with the receiver's reported
velocity components. This is a receiver consistency check. It compares
component changes without adding a model's transport or background
rotation. It neither ranks geometries nor measures full specific force.

Compare each path at the original time and at both signs of a fixed
0.4-second shift, the rounded magnitude from the earlier receiver
offset diagnosis. Retain identical whole-second receiver endpoints for
all paths and shifts at a given width. Require every shifted endpoint
inside the original interpolation support. Fit no time shift. Report
the discrepancy separately on the earlier and later partitions,
including both components, the horizontal RMS and the 95th percentile.
Use 0.02 m/s² only to describe scale. A force direction change of about
0.12° at one gravity has that transverse magnitude. This check cannot
turn disagreement between receivers into a calibrated error bound.

One task, one numerical thread, 19 precharged operations and a 120-second
cooperative cap. Bind the exact force-average and source receipts and the
qualified recovery files. Start no new Earth-model fits, decode no
original IMU packets, and use no reserved ESA measurements.
[Force averages](RF04_FORCE_AVERAGE_RESULT.md) · [Receiver offset](RF04_RECEIVER_OFFSET_RESULT.md)
